# app/routers/models.py
from __future__ import annotations

import os, shutil, zipfile, ast, queue, asyncio, traceback, subprocess
from io import BytesIO
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Literal, Optional

import pandas as pd
from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, HTTPException,
    UploadFile, status, Body, Request
)
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from pydantic import BaseModel, ValidationError, Field, model_validator
from ruamel.yaml import YAML
from sse_starlette.sse import EventSourceResponse
from sqlmodel import Session, select

from app.template_files import EVALUATE_PY
from app.auth import User, get_current_user
from app.db import SessionLocal
from app.models import (
    AIProject, ModelRun, DataSet, DataConfig, DataConfigCreate,
    ModelArtifact, TeamMembership
)
from app.utils.dependencies import get_session, assert_owner   # assert_owner = “propriétaire”
# ---------------------------------------------------------------------------

MAX_ZIP_SIZE = 50 * 1024 * 1024          # 50 MiB
REQUIRED_TEMPLATE_FILES = {"train.py", "model.py", "config.yaml", "requirements.txt"}

# ───────────────────────── helpers ─────────────────────────────────────────
def _assert_member(sess: Session, team_id: int, user: User) -> None:
    """403 si l’utilisateur n’est pas membre (invitation acceptée)."""
    mem = sess.exec(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not mem:
        raise HTTPException(403, "Accès interdit à cette équipe")

def to_docker_path(p: Path) -> str:
    s = str(p).replace("\\", "/")
    return f'"{s}"' if " " in s else s

# ───────────────────────── Router ──────────────────────────────────────────
router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/model",
    tags=["model"]
)

# ═════════════════════ Upload du code modèle ═══════════════════════════════
@router.post("/upload_model", status_code=200,
             summary="Upload du ZIP contenant le code du modèle")
async def upload_model_code(
    team_id: int,
    project_id: int,
    zip_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404, "Projet introuvable")
    if proj.owner != current_user.username:
        raise HTTPException(403, "Seul le propriétaire peut uploader le code")

    if zip_file.content_type not in ("application/zip", "application/x-zip-compressed"):
        raise HTTPException(400, "Il faut un fichier ZIP valide")

    tmp = NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        raw = await zip_file.read()
        if len(raw) > MAX_ZIP_SIZE:
            raise HTTPException(413, "Archive trop volumineuse (max 50 MiB)")

        try:
            zipfile.ZipFile(BytesIO(raw))
        except zipfile.BadZipFile:
            raise HTTPException(400, "ZIP corrompu ou invalide")

        tmp.write(raw); tmp.flush()

        with zipfile.ZipFile(tmp.name) as z:
            root_files = {Path(f).name for f in z.namelist() if "/" not in f.strip("/")}
            missing = REQUIRED_TEMPLATE_FILES - root_files
            if missing:
                return JSONResponse({"ok": False, "missing": sorted(missing)}, status_code=400)

            dest = Path(__file__).resolve().parents[2] / "storage" / "models" / f"project_{project_id}"
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True, exist_ok=True)
            z.extractall(dest)
            (dest / "evaluate.py").write_text(EVALUATE_PY, encoding="utf-8")
    finally:
        tmp.close(); Path(tmp.name).unlink(missing_ok=True)

    files = sorted(p.name for p in dest.iterdir() if p.is_file() and p.name != "evaluate.py")
    return {"ok": True, "files": files}

# ───────────────────── Vérif template avant upload ─────────────────────────
class TemplateCheckResult(BaseModel):
    ok: bool
    missing_files: List[str]
    missing_functions: List[str]

@router.post("/template/check", response_model=TemplateCheckResult)
async def check_model_template(
    team_id: int,
    project_id: int,
    zip_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404, "Projet introuvable")

    if zip_file.content_type not in ("application/zip", "application/x-zip-compressed"):
        raise HTTPException(400, "ZIP attendu")

    data = await zip_file.read()
    try:
        z = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile:
        raise HTTPException(400, "ZIP corrompu ou invalide")

    root_files = {Path(f).name for f in z.namelist() if "/" not in f.strip("/")}
    missing_files = sorted(REQUIRED_TEMPLATE_FILES - root_files)
    missing_funcs: list[str] = []

    if "train.py" in root_files and "def train_and_save_model" not in z.read("train.py").decode():
        missing_funcs.append("train_and_save_model()")
    if "model.py" in root_files and "class MyModel" not in z.read("model.py").decode():
        missing_funcs.append("class MyModel")

    return TemplateCheckResult(
        ok=not missing_files and not missing_funcs,
        missing_files=missing_files,
        missing_functions=missing_funcs,
    )

# ═════════════════════ Lancement d’entraînement ════════════════════════════
class TrainRequest(BaseModel):
    dataset_id: int

@router.post("/train", status_code=202)
def launch_training(
    team_id: int,
    project_id: int,
    payload: TrainRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404, "Projet introuvable")
    if proj.owner != current_user.username:
        raise HTTPException(403, "Seul le propriétaire peut lancer un entraînement")

    # quota de runs
    n_runs = sess.exec(select(ModelRun.id).where(ModelRun.project_id == project_id)).all()
    if len(n_runs) >= 10:
        raise HTTPException(403, "Quota de 10 runs atteint")

    ds = sess.get(DataSet, payload.dataset_id)
    if not ds or ds.project_id != project_id:
        raise HTTPException(400, "dataset_id invalide")

    run = ModelRun(project_id=project_id, status="pending")
    sess.add(run); sess.commit(); sess.refresh(run)

    background_tasks.add_task(_do_training, project_id, run.id, ds.path)
    return {"run_id": run.id, "status": run.status}



log_channels: dict[int, queue.SimpleQueue[str]] = {}        # run_id -> queue

def _do_training(project_id: int, run_id: int, train_data_path: str):
    """
    Tâche lancée en arrière-plan :
    - copie un snapshot des données pour la drift
    - démarre le conteneur Docker (image préinstallée smia-runtime:latest)
    - pousse chaque ligne de stdout dans une SimpleQueue
    - met à jour ModelRun à la fin
    """
    with SessionLocal() as sess:
        run = sess.get(ModelRun, run_id)
        run.started_at = datetime.utcnow()
        run.status = "running"
        sess.add(run)
        sess.commit()

    base_dir = Path(__file__).resolve().parents[2] / "storage" / "models" / f"project_{project_id}"
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # ─── 1) Snapshot pour la dérive ────────────────────────────────────────
    ref_stats = base_dir / "ref_stats.csv"
    q = log_channels.setdefault(run_id, queue.SimpleQueue())
    if not os.access(train_data_path, os.R_OK):
        q.put(f"Error: impossible de lire {train_data_path} (permission denied)")
    elif not os.access(base_dir, os.W_OK):
        q.put(f"Error: impossible d’écrire dans {base_dir} (permission denied)")
    else:
        try:
            shutil.copy(train_data_path, ref_stats)
            q.put(f"Snapshot ref_stats créé: {ref_stats.name}")
        except Exception:
            tb = traceback.format_exc()
            q.put("Warning: erreur lors du snapshot ref_stats (trace complète ci-dessous):")
            for line in tb.splitlines():
                q.put(line)

    code_path = to_docker_path(base_dir)
    data_path = to_docker_path(Path(train_data_path))
    output_path = to_docker_path(output_dir)
    cmd = [
        "docker", "run", "--rm",
        "--cpus=2.0", "--memory=4g", "--network=none",
        "--entrypoint", "/bin/sh",
        "-v", f"{code_path}:/code",
        "-v", f"{data_path}:/data/train.csv",
        "-v", f"{output_path}:/output",
        "smia-runtime:latest",
        "-c",
        (
            "pip install --no-cache-dir -r /code/requirements.txt && "
            "python /code/train.py "
            "--data /data/train.csv "
            "--config /code/config.yaml "
            "--out /output"
        )
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(proc.stdout.readline, ""):
            q.put(line.rstrip("\n"))
        ret_code = proc.wait(timeout=60 * 60)
    except subprocess.TimeoutExpired:
        proc.kill()
        q.put("Error: entraînement trop long (timeout 1 h)")
        ret_code = -1
    except Exception as exc:
        q.put(f"Error: exception lors de l'entraînement: {exc}")
        ret_code = -1

    q.put(f"Training finished, exit code = {ret_code}")

    # ─── 3) Recherche de l’artéfact ───────────────────────────────────────
    artifact_path = None
    for name in ("model.pt", "model.joblib", "model.onnx"):
        candidate = output_dir / name
        if candidate.exists():
            artifact_path = candidate
            break

    if artifact_path:
        size = artifact_path.stat().st_size
        basic_metrics = {"exit_code": ret_code}
        with SessionLocal() as sess:
            sess.add(ModelArtifact(
                project_id=project_id,
                model_run_id=run_id,
                path=str(artifact_path.resolve()),
                format=artifact_path.suffix.lstrip("."),
                size_bytes=size,
                metrics=basic_metrics,
            ))
            sess.commit()

    # ─── 4) Collecte des logs + MAJ ModelRun ─────────────────────────────
    collected = []
    while not q.empty():
        collected.append(q.get_nowait())
    log_channels.pop(run_id, None)

    with SessionLocal() as sess:
        run = sess.get(ModelRun, run_id)
        run.finished_at = datetime.utcnow()
        run.logs = "\n".join(collected)
        run.status = "succeeded" if ret_code == 0 else "failed"
        sess.add(run)
        sess.commit()

    # ─── record training duration into AIProject.ai_details ─────────────
    with SessionLocal() as sess3:
        from app.models import AIProject
        run = sess3.get(ModelRun, run_id)
        duration = (run.finished_at - run.started_at).total_seconds()

        proj = sess3.get(AIProject, project_id)
        existing = proj.ai_details
        if hasattr(existing, "dict"):
            data = existing.dict()
        else:
            data = existing or {}

        data["training_time"] = duration
        proj.ai_details = data
        sess3.add(proj)
        sess3.commit()


# ─────────────────────────── Consultation des runs ─────────────────────────

@router.get("/runs", response_model=List[ModelRun])
def list_runs(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    return sess.exec(
        select(ModelRun).where(ModelRun.project_id == project_id)
    ).all()



@router.get("/runs/{run_id}", response_model=ModelRun)
def get_run(
    team_id: int,
    project_id: int,
    run_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    run = sess.get(ModelRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Run introuvable")
    return run


# ─────────────────────────── Upload des datasets ───────────────────────────

# ─── Upload dataset
@router.post("/upload_dataset", status_code=201)
async def upload_dataset(
    team_id: int,
    project_id: int,
    kind: str = "train",
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)

    if kind not in {"train", "test"}:
        raise HTTPException(400, "kind doit être 'train' ou 'test'")

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404)

    if proj.owner != current_user.username:
        raise HTTPException(403, "Seul le propriétaire peut uploader un dataset")

    data_dir = Path(__file__).resolve().parents[2] / "storage" / "data" / f"project_{project_id}"
    data_dir.mkdir(parents=True, exist_ok=True)
    # on lit 1 MiB en premier pour vérifier la taille
    chunk = await file.read(1024 * 1024)

    if len(chunk) >= 1024 * 1024:

        raise HTTPException(413, "Fichier trop volumineux (>1 MiB)")
    rest = await file.read()
    data = chunk + rest
    # sniff CSV

    try:
        # essaie de lire un en-tête avec pandas
        pd.read_csv(BytesIO(data), nrows=5)
    except Exception:
        raise HTTPException(400, "Ce n'est pas un CSV valide")
    dest = data_dir / file.filename
    dest.write_bytes(data)

    # Lecture rapide de la tête pour récupérer les colonnes
    try:
        df = pd.read_csv(dest, nrows=5)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, f"Impossible de lire le CSV : {exc}")

    ds = DataSet(
        project_id=project_id,
        kind=kind,
        path=str(dest),
        columns=list(df.columns),
    )
    sess.add(ds)
    sess.commit()
    sess.refresh(ds)

    return {"dataset_id": ds.id, "columns": ds.columns}

# ───────────────────────── Lectures / écriture config.yaml ────────────────
yaml_ru = YAML()
yaml_ru.preserve_quotes = True


# --- schéma minimal attendu dans config.yaml
class ConfigSchema(BaseModel, extra="allow"):
    task: Literal["regression", "classification", "clustering"]
    target: Optional[str] = None
    hidden: int = Field(gt=0); lr: float = Field(gt=0); epochs: int = Field(gt=0)

    @model_validator(mode="after")
    def _target_needed(cls, v):
        if v.task in ("classification", "regression") and not v.target:
            raise ValueError("`target` requis pour cette tâche")
        return v

def _config_path(project_id: int) -> Path:
    return Path(__file__).resolve().parents[2] / "storage" / "models" / f"project_{project_id}" / "config.yaml"

@router.get("/config", response_class=PlainTextResponse)
def read_config_yaml(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    path = _config_path(project_id)
    if not path.exists():
        raise HTTPException(404, "config.yaml introuvable")
    return path.read_text(encoding="utf-8")

@router.put("/config")
def update_config_yaml(
    team_id: int,
    project_id: int,
    body: str = Body(..., media_type="text/plain"),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # seule la/le propriétaire peut modifier
    assert_owner(sess, project_id, current_user)

    try:
        data = yaml_ru.load(body)
        ConfigSchema.model_validate(data)
    except ValidationError as ex:
        raise HTTPException(422, ex.errors())
    except Exception as ex:
        raise HTTPException(400, f"YAML invalide : {ex}")

    path = _config_path(project_id)
    if not path.exists():
        raise HTTPException(404, "config.yaml introuvable")

    with path.open("w", encoding="utf-8") as f:
        yaml_ru.dump(data, f)
    return {"ok": True}

# ─── DataConfig
@router.post("/data_config", response_model=DataConfig)
def upsert_data_config(
    team_id: int,
    project_id: int,
    cfg: DataConfigCreate,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)   # propriétaire uniquement

    # 1) vérifie dataset appartient au projet
    train_ds = sess.get(DataSet, cfg.train_dataset_id)
    test_ds = sess.get(DataSet, cfg.test_dataset_id)
    if not train_ds or train_ds.project_id != project_id or train_ds.kind != "train":
        raise HTTPException(400, "train_dataset_id invalide")
    if not test_ds or test_ds.project_id != project_id or test_ds.kind != "test":
        raise HTTPException(400, "test_dataset_id invalide")

    # 2) vérifie que target et features existent dans ds.columns
    for col in [cfg.target, *cfg.features, *cfg.sensitive_attrs]:
        if col not in train_ds.columns:
            raise HTTPException(422, f"Colonne inconnue: {col}")

    # 3) upsert
    dc = sess.exec(
        select(DataConfig).where(DataConfig.train_dataset_id == cfg.train_dataset_id)
    ).first()
    if dc:
        for k, v in cfg.model_dump().items():
            setattr(dc, k, v)
    else:
        dc = DataConfig.model_validate(cfg)
    sess.add(dc);
    sess.commit();
    sess.refresh(dc)
    return dc


@router.get("/data_config", response_model=DataConfig)
def get_data_config(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    dc = sess.exec(
        select(DataConfig).join(DataSet).where(DataSet.project_id == project_id)
    ).first()
    if not dc:
        raise HTTPException(404, "DataConfig non trouvé")
    return dc

# ─── Stream logs
@router.get("/runs/{run_id}/stream", response_class=EventSourceResponse)
async def stream_logs(
    team_id: int,
    project_id: int,
    run_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)

    q = log_channels.get(run_id)
    if q is None:
        raise HTTPException(404, "Run inconnu ou pas démarré")

    loop = asyncio.get_running_loop()

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            line = await loop.run_in_executor(None, q.get)
            yield {"data": line}

    return EventSourceResponse(event_generator())