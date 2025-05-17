# app/routers/evaluations.py
import shlex
import subprocess
import queue
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import matplotlib.pyplot as plt
from lime.lime_tabular import LimeTabularExplainer
import sys
import importlib
import importlib.util
import pandas as pd
import torch
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlmodel import Session, select
import yaml
from app.auth import User, get_current_user
from app.db import SessionLocal
from importlib import import_module
from app.metrics.pipeline import analyze, _HAS_SHAP
from app.models import (
    AIProject,
    ModelRun,
    DataSet,
    DataConfig,
    EvaluationRun,
    ModelArtifact,
)
from fastapi.responses import FileResponse
from typing import List
from app.utils.dependencies import assert_owner, get_session
from pydantic import BaseModel
import asyncio
import json as js
router = APIRouter(
    prefix="/projects/{project_id}",
    tags=["evaluations"],
    responses={404: {"description": "Not found"}},
)

# file_id -> queue
eval_log_channels: dict[int, queue.SimpleQueue[str]] = {}
# helper
def to_docker_path(p: Path) -> str:
    # 1) C:\dir\file → C:/dir/file
    # 2) entoure de guillemets si le chemin contient un espace
    s = str(p).replace("\\", "/")
    return f'"{s}"' if " " in s else s

class EvaluateRequest(BaseModel):
    model_run_id: int
    test_data_id: int
    data_config_id: int


@router.post(
    "/evaluate",
    status_code=202,
    summary="Lance une évaluation en tâche de fond",
)
def launch_evaluation(
    project_id: int,
    payload: EvaluateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # droits & validité des références
    assert_owner(sess, project_id, current_user)

    # existe bien run, dataset et config ?
    run = sess.get(ModelRun, payload.model_run_id)
    ds = sess.get(DataSet, payload.test_data_id)
    cfg = sess.get(DataConfig, payload.data_config_id)
    if not run or run.project_id != project_id:
        raise HTTPException(400, "model_run_id invalide")
    if not ds or ds.project_id != project_id or ds.kind != "test":
        raise HTTPException(400, "test_data_id invalide")
    if not cfg or cfg.dataset_id != ds.id:
        raise HTTPException(400, "data_config_id invalide")

    # créer l'EvaluationRun
    eval_run = EvaluationRun(
        project_id=project_id,
        model_run_id=payload.model_run_id,
        status="pending",
    )
    sess.add(eval_run)
    sess.commit()
    sess.refresh(eval_run)

    # lancer en arrière-plan
    background_tasks.add_task(
        _do_evaluation,
        project_id,
        eval_run.id,
        payload.model_run_id,
        payload.test_data_id,
        payload.data_config_id,
    )

    return {"eval_id": eval_run.id, "status": eval_run.status}

def _do_evaluation(
    project_id: int,
    eval_id: int,
    model_run_id: int,
    test_data_id: int,
    data_config_id: int,
):
    """
    Exécute l’évaluation DANS le conteneur Docker `smia-runtime:latest`
    en appelant <repo-modèle>/evaluate.py.

    Le script evaluate.py doit :

      • charger le modèle (+ config)
      • charger le CSV de test
      • appeler `analyze()`
      • écrire un JSON  →   /code/output/eval_metrics.json
      • écrire les PNG   →  /code/output/{shap_summary.png|lime_local.png|…}
    """
    # ─────────────────────────── 1) marque démarrage ───────────────────────
    with SessionLocal() as sess:
        er = sess.get(EvaluationRun, eval_id)
        er.started_at = datetime.utcnow()
        er.status = "running"
        sess.add(er); sess.commit()

    # ─────────────────────────── 2) artefact / dataset / cfg ───────────────
    q = eval_log_channels.setdefault(eval_id, queue.SimpleQueue())
    with SessionLocal() as sess:
        art = (
            sess.exec(
                select(ModelArtifact)
                .where(ModelArtifact.model_run_id == model_run_id)
                .order_by(ModelArtifact.created_at.desc())
            )
            .first()
        )
        if not art or not Path(art.path).exists():
            er = sess.get(EvaluationRun, eval_id)
            er.status = "failed"
            er.logs = "Artifact missing"
            er.finished_at = datetime.utcnow()
            sess.add(er); sess.commit()
            return

        model_dir   = Path(art.path).parent.parent                 # …/storage/models/project_{id}
        model_path  = model_dir / "output" / "model.pt"
        ds          = sess.get(DataSet, test_data_id)
        cfg         = sess.get(DataConfig, data_config_id)
        cfg_data = {
            "features": cfg.features,
            "sensitive_attrs": cfg.sensitive_attrs,
        }
        cd_path = model_dir / "config_data.json"
        with open(cd_path, "w", encoding="utf-8") as f:
            js.dump(cfg_data, f)
        q.put(f"Config data dumpé → {cd_path.name}")

    # ─────────────────────────── 3) file SSE ───────────────────────────────
    q.put("Starting Docker evaluation job…")

    # ─────────────────────────── 4) appel Docker ───────────────────────────
    output_dir  = model_dir / "output"
    metrics_json = output_dir / "metrics.json"

    # ► conversions chemin-hôte → format accepté par Docker
    code_path = to_docker_path(model_dir)  # même nom que plus bas = plus clair
    data_path = to_docker_path(Path(ds.path))
    output_path = to_docker_path(output_dir)

    cmd = [
        "docker", "run", "--rm",
        "--cpus=2.0", "--memory=4g", "--network=none",
        "--entrypoint", "/bin/sh",

        "-v", f"{code_path}:/code",
        "-v", f"{data_path}:/data/test.csv",
        "-v", f"{output_path}:/output",
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

    # on log la commande pour debug éventuel
    q.put(f"Docker CMD: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # on récupère les lignes au fil de l’eau
        for line in iter(proc.stdout.readline, ""):
            q.put(line.rstrip("\n"))
        # impose un timeout de 30 min
        exit_code = proc.wait(timeout=30 * 60)
    except subprocess.TimeoutExpired:
        proc.kill()
        q.put("Error: évaluation trop longue (timeout 30 min)")
        exit_code = -1
    except Exception as exc:
        q.put(f"Error: exception lors de l'évaluation: {exc}")
        exit_code = -1

    q.put(f"Docker exited with code {exit_code}")

    # ─────────────────────────── 5) post-processing ────────────────────────
    if exit_code != 0 or not metrics_json.exists():
        # échec → status failed
        collected = []
        while not q.empty():
            collected.append(q.get())
        eval_log_channels.pop(eval_id, None)
        with SessionLocal() as sess:
            er = sess.get(EvaluationRun, eval_id)
            er.finished_at = datetime.utcnow()
            er.status = "failed"
            er.logs = "\n".join(collected)
            sess.add(er); sess.commit()
        return

    # charge les métriques JSON
    import json

    with metrics_json.open() as f:
        metrics: Dict[str, Any] = json.load(f)

    # ─────────────────────────── 6) FIN & persistance ──────────────────────
    q.put("Evaluation finished – metrics collected.")
    collected = []
    while not q.empty():
        collected.append(q.get())
    eval_log_channels.pop(eval_id, None)

    with SessionLocal() as sess:
        er = sess.get(EvaluationRun, eval_id)
        er.finished_at = datetime.utcnow()
        er.status = "succeeded"
        er.logs = "\n".join(collected)
        er.metrics = metrics
        sess.add(er); sess.commit()


@router.get(
    "/evaluations/{eval_id}/stream",
    response_class=EventSourceResponse,
    summary="Stream SSE des logs d'évaluation",
)
async def stream_eval_logs(
    project_id: int,
    eval_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)
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

# 1) Lister les évaluations d’un projet
@router.get(
    "/evaluations",
    response_model=List[EvaluationRun],
    summary="Liste des évaluations"
)
def list_evaluations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)
    return sess.exec(
        select(EvaluationRun).where(EvaluationRun.project_id == project_id)
    ).all()


# 2) Détail d’une évaluation (métadonnées + metrics agrégées)
@router.get(
    "/evaluations/{eval_id}",
    response_model=EvaluationRun,
    summary="Détail d’une évaluation"
)
def get_evaluation(
    project_id: int,
    eval_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    er = sess.get(EvaluationRun, eval_id)
    if not er or er.project_id != project_id:
        raise HTTPException(404, "Évaluation non trouvée")
    return er


# 3) Récupérer un graphique pré-calculé
@router.get(
    "/evaluations/{eval_id}/plots/{plot_name}",
    summary="Télécharge un plot pré-calculé (e.g. shap_summary, lime_local)"
)
def get_evaluation_plot(
    project_id: int,
    eval_id: int,
    plot_name: str,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    er = sess.get(EvaluationRun, eval_id)
    if not er or er.project_id != project_id:
        raise HTTPException(404, "Évaluation non trouvée")

    # On s’attend à stocker dans er.metrics["explainability"]
    # les clés "{plot_name}_plot" pointant vers un chemin existant
    path = (
        er.metrics
        .get("explainability", {})
        .get(f"{plot_name}_plot")
    )
    if not path:
        raise HTTPException(404, f"Plot « {plot_name} » introuvable")
    return FileResponse(path, media_type="image/png")