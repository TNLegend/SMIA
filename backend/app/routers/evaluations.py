# app/routers/evaluations.py
from __future__ import annotations

import asyncio
import json as js
import queue
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlmodel import Session, select

from app.auth import User, get_current_user
from app.db import SessionLocal
from app.models import (
    AIProject,
    DataConfig,
    DataSet,
    EvaluationRun,
    ModelArtifact,
    ModelRun,
    TeamMembership,
)
from app.utils.dependencies import get_session, assert_owner  # assert_owner = « propriétaire »

# ───────────────────────── helpers ──────────────────────────────────────────
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
    """Chemin Windows → chemin Docker safe."""
    s = str(p).replace("\\", "/")
    return f'"{s}"' if " " in s else s


# ───────────────────────── Router ───────────────────────────────────────────
router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}",
    tags=["evaluations"],
    responses={404: {"description": "Not found"}},
)

# --------------------------------------------------------------model/runs/-------------

eval_log_channels: dict[int, queue.SimpleQueue[str]] = {}  # eval_id -> queue


class EvaluateRequest(BaseModel):
    model_run_id: int
    data_config_id: int


# ═════════════════════ Lancer une évaluation ═══════════════════════════════
@router.post(
    "/evaluate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Lance une évaluation en tâche de fond (réservé au propriétaire)",
)
def launch_evaluation(
    team_id: int,
    project_id: int,
    payload: EvaluateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)      # doit être membre
    assert_owner(sess, project_id, current_user)     # et propriétaire

    # Vérifie que le projet appartient bien à l’équipe
    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404, "Projet introuvable")

    # 1) ModelRun présent et lié
    run = sess.get(ModelRun, payload.model_run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(400, "model_run_id invalide")

    # 2) DataConfig présent et lié
    cfg = sess.get(DataConfig, payload.data_config_id)
    if not cfg:
        raise HTTPException(400, "data_config_id invalide")
    if cfg.train_dataset.project_id != project_id or cfg.test_dataset.project_id != project_id:
        raise HTTPException(400, "DataConfig ne correspond pas à ce projet")

    # 3) Création EvaluationRun
    eval_run = EvaluationRun(
        project_id=project_id,
        model_run_id=payload.model_run_id,
        status="pending",
    )
    sess.add(eval_run)
    sess.commit()
    sess.refresh(eval_run)

    # 4) Task async
    background_tasks.add_task(
        _do_evaluation,
        project_id,
        eval_run.id,
        payload.model_run_id,
        cfg.test_dataset_id,
        payload.data_config_id,
    )

    return {"eval_id": eval_run.id, "status": eval_run.status}


# ---------------------------------------------------------------------------
def _do_evaluation(
    project_id: int,
    eval_id: int,
    model_run_id: int,
    test_data_id: int,
    data_config_id: int,
) -> None:
    """
    Exécute l’évaluation DANS le conteneur Docker `smia-runtime:latest`
    en appelant <repo-modèle>/evaluate.py.
    """
    q = eval_log_channels.setdefault(eval_id, queue.SimpleQueue())
    all_logs: list[str] = []

    def push(msg: str) -> None:
        q.put(msg)
        all_logs.append(msg)

    # 1) marque démarrage
    with SessionLocal() as sess:
        er = sess.get(EvaluationRun, eval_id)
        er.started_at = datetime.utcnow()
        er.status = "running"
        sess.add(er)
        sess.commit()
    push(f"Evaluation {eval_id} started at {datetime.utcnow().isoformat()}")

    # 2) artefact / dataset / cfg lookup
    with SessionLocal() as sess:
        art = sess.exec(
            select(ModelArtifact)
            .where(ModelArtifact.model_run_id == model_run_id)
            .order_by(ModelArtifact.created_at.desc())
        ).first()
        if not art or not Path(art.path).exists():
            er = sess.get(EvaluationRun, eval_id)
            er.status = "failed"
            er.logs = "Artifact missing"
            er.finished_at = datetime.utcnow()
            sess.add(er)
            sess.commit()
            push("🛑 Artifact missing, aborting evaluation.")
            eval_log_channels.pop(eval_id, None)
            return

        model_dir = Path(art.path).parent.parent
        ds = sess.get(DataSet, test_data_id)
        cfg = sess.get(DataConfig, data_config_id)

    # dump config_data.json
    cfg_data = {"features": cfg.features, "sensitive_attrs": cfg.sensitive_attrs}
    cd_path = model_dir / "config_data.json"
    cd_path.write_text(js.dumps(cfg_data, indent=2), encoding="utf-8")
    push(f"Config data dumped → {cd_path.name}")

    # 3) lancement du conteneur Docker
    output_dir = model_dir / "output"
    metrics_json = output_dir / "metrics.json"

    host_app_dir = Path(__file__).resolve().parents[2]
    cmd = [
        "docker",
        "run",
        "--rm",
        "--cpus=2.0",
        "--memory=4g",
        "--network=none",
        "--entrypoint",
        "/bin/sh",
        "-v",
        f"{to_docker_path(host_app_dir)}:/app",
        "-v",
        f"{to_docker_path(model_dir)}:/code",
        "-v",
        f"{to_docker_path(Path(ds.path))}:/data/test.csv",
        "-v",
        f"{to_docker_path(output_dir)}:/output",
        "smia-runtime:latest",
        "-c",
        (
            "pip install --no-cache-dir -r /code/requirements.txt && "
            "python /code/evaluate.py "
            "--model  /code/output/model.pt "
            "--test   /data/test.csv "
            "--config /code/config.yaml "
            "--out    /output"
        ),
    ]
    push(f"Docker CMD: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(proc.stdout.readline, ""):
            push(line.rstrip("\n"))
        exit_code = proc.wait(timeout=30 * 60)  # 30 min max
    except subprocess.TimeoutExpired:
        proc.kill()
        push("Error: évaluation trop longue (timeout 30 min)")
        exit_code = -1
    except Exception as exc:
        push(f"Error: exception lors de l'évaluation: {exc}")
        exit_code = -1

    push(f"Docker exited with code {exit_code}")

    # 4) échec ?
    if exit_code != 0 or not metrics_json.exists():
        with SessionLocal() as sess:
            er = sess.get(EvaluationRun, eval_id)
            er.finished_at = datetime.utcnow()
            er.status = "failed"
            er.logs = "\n".join(all_logs)
            sess.add(er)
            sess.commit()
        push("🛑 Evaluation failed, logs persisted.")
        eval_log_channels.pop(eval_id, None)
        return

    # 5) succès → lecture et persistance des metrics
    metrics = js.loads(metrics_json.read_text(encoding="utf-8"))
    push("Evaluation finished – metrics collected.")

    with SessionLocal() as sess:
        er = sess.get(EvaluationRun, eval_id)
        er.finished_at = datetime.utcnow()
        er.status = "succeeded"
        er.logs = "\n".join(all_logs)
        er.metrics = metrics
        sess.add(er)
        sess.commit()

    # ─── mise à jour AIProject.ai_details ─────────────────────────────────
    with SessionLocal() as sess2:
        proj = sess2.get(AIProject, project_id)

        train_run = sess2.get(ModelRun, model_run_id)
        training_time = (
            (train_run.finished_at - train_run.started_at).total_seconds()
            if train_run and train_run.started_at and train_run.finished_at
            else 0.0
        )

        cfg = sess2.get(DataConfig, data_config_id)

        proj.ai_details = {
            "type": metrics.get("task", "unknown"),
            "model": metrics.get("model_name"),
            "framework": "PyTorch",
            "dataset_size": int(metrics.get("dataset_size", 0)),
            "features_count": len(cfg.features),
            "accuracy": float(metrics.get("accuracy", 0.0)),
            "r2": float(metrics.get("r2", 0.0)),
            "training_time": training_time,
        }
        sess2.add(proj)
        sess2.commit()

    push("✅ All done.")
    eval_log_channels.pop(eval_id, None)


# ═════════════════════ Endpoints de lecture (membres) ═══════════════════════
@router.get("/evaluations", response_model=List[EvaluationRun])
def list_evaluations(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    return sess.exec(
        select(EvaluationRun).where(EvaluationRun.project_id == project_id)
    ).all()


@router.get("/evaluations/{eval_id}", response_model=EvaluationRun)
def get_evaluation(
    team_id: int,
    project_id: int,
    eval_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    er = sess.get(EvaluationRun, eval_id)
    if not er or er.project_id != project_id:
        raise HTTPException(404, "Évaluation non trouvée")
    return er


@router.get(
    "/evaluations/{eval_id}/plots/{plot_name}",
    response_class=FileResponse,
    summary="Télécharge un plot pré-calculé (p. ex. shap_summary.png)",
)
def get_evaluation_plot(
    team_id: int,
    project_id: int,
    eval_id: int,
    plot_name: str,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)
    er = sess.get(EvaluationRun, eval_id)
    if not er or er.project_id != project_id:
        raise HTTPException(404, "Évaluation non trouvée")

    art = sess.exec(
        select(ModelArtifact)
        .where(ModelArtifact.model_run_id == er.model_run_id)
        .order_by(ModelArtifact.created_at.desc())
    ).first()
    if not art:
        raise HTTPException(404, "Artifact introuvable pour cette évaluation")

    host_plot = Path(art.path).parent.parent / "output" / f"{plot_name}.png"
    if not host_plot.exists():
        raise HTTPException(404, "Plot introuvable")

    return FileResponse(str(host_plot), media_type="image/png")


# ═════════════════════ Stream SSE des logs ═════════════════════════════════
@router.get(
    "/evaluations/{eval_id}/stream",
    response_class=EventSourceResponse,
    summary="Stream SSE des logs d'évaluation",
)
async def stream_eval_logs(
    team_id: int,
    project_id: int,
    eval_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)

    q = eval_log_channels.get(eval_id)
    if q is None:
        raise HTTPException(404, "Évaluation inconnue ou non démarrée")

    loop = asyncio.get_running_loop()

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            line = await loop.run_in_executor(None, q.get)
            yield {"data": line}

    return EventSourceResponse(event_generator())
