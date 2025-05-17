# app/routers/models.py

import os
import shutil
import zipfile , ast
from io import BytesIO
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List
import queue
import pandas as pd
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status, Body,Request
)
from fastapi.responses import JSONResponse,Response
from pydantic import BaseModel, ValidationError, Field
from sqlmodel import Session, select
from app.template_files import EVALUATE_PY
from app.auth import User, get_current_user
from app.db import SessionLocal
from app.models import AIProject, ModelRun, DataSet, DataConfig, DataConfigCreate, ModelArtifact
from ruamel.yaml import YAML
from sse_starlette.sse import EventSourceResponse
import asyncio
from app.utils.dependencies import assert_owner,get_session
import traceback
from fastapi.responses import PlainTextResponse

MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50 MiB
REQUIRED_TEMPLATE_FILES = {"train.py", "model.py", "config.yaml", "requirements.txt"}

# ────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/projects/{project_id}/model", tags=["model"])


def to_docker_path(p: Path) -> str:
    # 1) C:\dir\file → C:/dir/file
    # 2) entoure de guillemets si le chemin contient un espace
    s = str(p).replace("\\", "/")
    return f'"{s}"' if " " in s else s
# ─────────────────────────── Upload du code modèle ─────────────────────────

@router.post("/upload_model", status_code=200, summary="Upload du ZIP contenant le code du modèle")
async def upload_model_code(
    project_id: int,
    zip_file: UploadFile = File(..., description="Archive .zip avec train.py, model.py, config.yaml, requirements.txt"),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # Vérification des droits
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projet introuvable")
    if proj.owner != current_user.username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès interdit")
        # header Content-Type
    if zip_file.content_type not in ("application/zip", "application/x-zip-compressed"):
        raise HTTPException(400, "Il faut un .zip valide")

    # Sauvegarde temporaire du zip
    tmp = NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        raw = await zip_file.read()
        if len(raw) > MAX_ZIP_SIZE:

            raise HTTPException(413, "Archive trop volumineuse (max 50 MiB)")
          # sniff MIME type

        # pour ZIP
        try:
            z = zipfile.ZipFile(BytesIO(raw))
        except zipfile.BadZipFile:
            raise HTTPException(400, "Ce n'est pas un ZIP valide ou le fichier est corrompu")
        tmp.write(raw)
        tmp.flush()

        with zipfile.ZipFile(tmp.name) as z:
            root_files = {Path(f).name for f in z.namelist() if "/" not in f.strip("/")}
            missing = REQUIRED_TEMPLATE_FILES - root_files
            if missing:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "missing": sorted(missing)},
                )

            dest = Path(__file__).resolve().parents[2] / "storage" / "models" / f"project_{project_id}"
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True, exist_ok=True)
            z.extractall(dest)
            (dest / "evaluate.py").write_text(EVALUATE_PY, encoding="utf-8")

    finally:
        tmp.close()
        Path(tmp.name).unlink(missing_ok=True)

    return {"ok": True, "files": sorted(p.name for p in dest.iterdir())}

class TemplateCheckResult(BaseModel):
    ok: bool
    missing_files: List[str]
    missing_functions: List[str]

@router.post(
    "/template/check",
    summary="Vérifie un ZIP modèle avant upload",
    response_model=TemplateCheckResult,
)
async def check_model_template(
    project_id: int,
    zip_file: UploadFile = File(..., description="Archive ZIP à vérifier"),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # droits
    assert_owner(sess, project_id, current_user)

    # 1) vérif du type
    if zip_file.content_type not in  ["application/zip","application/x-zip-compressed"]:
        raise HTTPException(400, "Il faut un fichier ZIP valide (.zip)")
    data = await zip_file.read()

    # 2) ouverture du ZIP
    try:
        z = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile:
        raise HTTPException(400, "Fichier ZIP corrompu ou invalide")

    # 3) fichiers racine attendus
    root_files = { Path(f).name for f in z.namelist() if "/" not in f.strip("/") }
    missing_files = sorted(REQUIRED_TEMPLATE_FILES - root_files)

    # 4) vérif des signatures dans train.py et model.py
    missing_functions: list[str] = []

    if "train.py" in root_files:
        src = z.read("train.py").decode("utf-8")
        tree = ast.parse(src)
        if not any(isinstance(n, ast.FunctionDef) and n.name == "train_and_save_model" for n in tree.body):
            missing_functions.append("train_and_save_model()")

    if "model.py" in root_files:
        src = z.read("model.py").decode("utf-8")
        tree = ast.parse(src)
        if not any(isinstance(n, ast.ClassDef) and n.name == "MyModel" for n in tree.body):
            missing_functions.append("class MyModel")

    return TemplateCheckResult(
        ok=not missing_files and not missing_functions,
        missing_files=missing_files,
        missing_functions=missing_functions,
    )
# ─────────────────────────── Lancement d’entraînement ──────────────────────

class TrainRequest(BaseModel):
    dataset_id: int


@router.post("/train", status_code=202, summary="Démarre l’entraînement en tâche de fond")
def launch_training(
    project_id: int,
    payload: TrainRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # 1) droits et existence du projet
    proj = sess.get(AIProject, project_id)
    if not proj or proj.owner != current_user.username:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
     # quota max de runs simultanés
    existing = sess.exec(
             select(ModelRun).where(ModelRun.project_id == project_id)
        ).all()
    if len(existing) >= 10:
        raise HTTPException(403, "Vous avez déjà 10 runs actifs, supprimez-en avant d'en lancer un autre")
    # 3) lookup du dataset
    ds = sess.get(DataSet, payload.dataset_id)

    if not ds or ds.project_id != project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "dataset_id invalide")
    # 4) création du ModelRun
    run = ModelRun(project_id=project_id, status="pending")
    sess.add(run)
    sess.commit()
    sess.refresh(run)
    # 5) on passe le chemin absolu au background task
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
        sess.add(run); sess.commit()

    base_dir = Path(__file__).resolve().parents[2] / "storage" / "models" / f"project_{project_id}"
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # ─── 1) Snapshot pour la dérive ────────────────────────────────────────
    ref_stats = base_dir / "ref_stats.csv"
    q = log_channels.setdefault(run_id, queue.SimpleQueue())
    # 1) le fichier d’entraînement doit être lisible
    if not os.access(train_data_path, os.R_OK):
        q.put(f"Error: impossible de lire {train_data_path} (permission denied)")
    # 2) le dossier base_dir doit être inscriptible
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

    # mount the project dir as /code, then inside the container:
    # 1) install the user’s requirements.txt
    # 2) run train.py
    code_path = to_docker_path(base_dir)
    data_path = to_docker_path(Path(train_data_path))
    output_path = to_docker_path(output_dir)
    cmd = [
        "docker", "run", "--rm",
        "--cpus=2.0", "--memory=4g", "--network=none",

        # ⬇️  Écrase complètement l’ENTRYPOINT défini dans l’image
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
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in iter(proc.stdout.readline, ""):
            q.put(line.rstrip("\n"))
        # timeout après 1 h
        ret_code = proc.wait(timeout=60 * 60)
    except subprocess.TimeoutExpired:
        proc.kill()
        q.put("Error: entraînement trop long (timeout 1 h)")
        ret_code = -1
    except Exception as exc:
        q.put(f"Error: exception lors de l'entraînement: {exc}")
        ret_code = -1

    q.put(f"Training finished, exit code = {ret_code}")

    # ─── 3) Recherche déterministe de l'artefact ───────────────────────────
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
            sess.add(
                ModelArtifact(
                    project_id=project_id,
                    model_run_id=run_id,
                    path=str(artifact_path.resolve()),
                    format=artifact_path.suffix.lstrip("."),
                    size_bytes=size,
                    metrics=basic_metrics,
                )
            )
            sess.commit()

    # ─── 4) Collecte des logs et mise à jour finale ────────────────────────
    collected = []
    while not q.empty():
        collected.append(q.get_nowait())
    log_channels.pop(run_id, None)

    with SessionLocal() as sess:
        run = sess.get(ModelRun, run_id)
        run.finished_at = datetime.utcnow()
        run.logs = "\n".join(collected)
        run.status = "succeeded" if ret_code == 0 else "failed"
        sess.add(run); sess.commit()


# ─────────────────────────── Consultation des runs ─────────────────────────

@router.get("/runs", response_model=List[ModelRun], summary="Liste des runs d’entraînement")
def list_runs(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    if not sess.get(AIProject, project_id):
        raise HTTPException(404, "Projet introuvable")
    return sess.exec(select(ModelRun).where(ModelRun.project_id == project_id)).all()


@router.get("/runs/{run_id}", response_model=ModelRun, summary="Détail d’un run")
def get_run(
    project_id: int,
    run_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    run = sess.get(ModelRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Run introuvable")
    return run


# ─────────────────────────── Upload des datasets ───────────────────────────

@router.post("/upload_dataset", status_code=201, summary="Upload d’un dataset (train ou test)")
async def upload_dataset(
    project_id: int,
    kind: str = "train",  # ?kind=train|test
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    if kind not in {"train", "test"}:
        raise HTTPException(400, "kind doit être 'train' ou 'test'")

    proj = sess.get(AIProject, project_id)
    if not proj or proj.owner != current_user.username:
        raise HTTPException(403)

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
    target: str
    hidden: int = Field(gt=0)
    lr: float = Field(gt=0)
    epochs: int = Field(gt=0)


def _config_path(project_id: int) -> Path:
    base = Path(__file__).resolve().parents[2] / "storage" / "models" / f"project_{project_id}"
    return base / "config.yaml"


@router.get("/config", response_class=PlainTextResponse, summary="Récupère le YAML brut")
def read_config_yaml(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)  # petite fonction utilitaire
    path = _config_path(project_id)
    if not path.exists():
        raise HTTPException(404, "config.yaml introuvable – uploadez d’abord le modèle")
    return path.read_text(encoding="utf-8")


@router.put("/config", summary="Met à jour le YAML après validation")
def update_config_yaml(
    project_id: int,
    body: str = Body(..., media_type="text/plain"),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)
    try:
        data = yaml_ru.load(body)
    except Exception as exc:
        raise HTTPException(400, f"YAML syntaxe invalide : {exc}")

    # Validation pydantic
    try:
        ConfigSchema.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(422, exc.errors())

    path = _config_path(project_id)
    if not path.exists():
        raise HTTPException(404, "config.yaml introuvable – uploadez d’abord le modèle")

    # Écrire tout en conservant l’ordre et les commentaires
    with _config_path(project_id).open("w", encoding="utf-8") as f:
        yaml_ru.dump(data, f)
    return {"ok": True}

# ───────────────────────── DATA CONFIG ────────────────
@router.post("/data_config", response_model=DataConfig)
def upsert_data_config(
    project_id: int,
    cfg: DataConfigCreate,                 # pydantic model avec dataset_id, …
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)

    # 1) vérifie dataset appartient au projet
    ds = sess.get(DataSet, cfg.dataset_id)
    if not ds or ds.project_id != project_id:
        raise HTTPException(400, "dataset_id invalide")

    # 2) vérifie que target et features existent dans ds.columns
    for col in [cfg.target, *cfg.features, *cfg.sensitive_attrs]:
        if col not in ds.columns:
            raise HTTPException(422, f"Colonne inconnue: {col}")

    # 3) upsert
    dc = sess.exec(
        select(DataConfig).where(DataConfig.dataset_id == cfg.dataset_id)
    ).first()
    if dc:
        for k, v in cfg.model_dump().items():
            setattr(dc, k, v)
    else:
        dc = DataConfig.model_validate(cfg)
    sess.add(dc); sess.commit(); sess.refresh(dc)
    return dc


@router.get("/data_config", response_model=DataConfig)
def get_data_config(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)
    dc = sess.exec(
        select(DataConfig).join(DataSet).where(DataSet.project_id == project_id)
    ).first()
    if not dc:
        raise HTTPException(404, "DataConfig non trouvé")
    return dc

@router.get("/runs/{run_id}/stream", response_class=EventSourceResponse)
async def stream_logs(
    project_id: int,
    run_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)

    q = log_channels.get(run_id)
    if q is None:
        raise HTTPException(404, "Run inconnu ou pas démarré")

    loop = asyncio.get_running_loop()

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            # lit la file dans un thread pool pour ne pas bloquer la boucle
            line = await loop.run_in_executor(None, q.get)
            yield {"data": line}

    return EventSourceResponse(event_generator())
