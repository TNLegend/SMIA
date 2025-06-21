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
# `sse_starlette` est une dépendance clé pour envoyer des logs en temps réel au client (Server-Sent Events).
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
from app.utils.dependencies import get_session, assert_owner

# ───────────────────────── Helpers & Configuration Globale ───────────────────────────────────

def _assert_member(sess: Session, team_id: int, user: User) -> None:
    """Helper de sécurité : 403 si l’utilisateur n’est pas un membre actif de l'équipe."""
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
    """Helper de compatibilité : Convertit un chemin de fichier Windows (avec `\`)
    en un chemin compatible avec les systèmes Unix/Docker (avec `/`)."""
    return str(p).replace("\\", "/")

# BLOC D'ÉTAT GLOBAL POUR LES LOGS EN TEMPS RÉEL
# Ce dictionnaire est un composant crucial pour le streaming des logs.
# Il associe un ID d'évaluation (`eval_id`) à une file d'attente (`queue`).
# La tâche de fond écrira les logs dans la file, et une autre route (SSE)
# lira les logs depuis cette même file pour les envoyer au client.
eval_log_channels: dict[int, queue.SimpleQueue[str]] = {}

# ───────────────────────── Router & Modèles de Données ───────────────────────────────────────────

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}",
    tags=["evaluations"],
    responses={404: {"description": "Not found"}},
)

class EvaluateRequest(BaseModel):
    """Définit la structure de la requête pour lancer une évaluation."""
    model_run_id: int
    data_config_id: int


# ═════════════════════ Lancement d'une Évaluation (Tâche de Fond) ═══════════════════════════════
@router.post(
    "/evaluate",
    status_code=status.HTTP_202_ACCEPTED, # 202 indique que la requête est acceptée pour traitement mais pas encore terminée.
    summary="Lance une évaluation en tâche de fond (réservé au propriétaire)",
)
def launch_evaluation(
    team_id: int,
    project_id: int,
    payload: EvaluateRequest,
    background_tasks: BackgroundTasks, # Dépendance FastAPI pour exécuter des tâches après avoir envoyé la réponse.
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # BLOC DE LANCEMENT D'UNE ÉVALUATION ASYNCHRONE
    # Cette route ne fait pas l'évaluation elle-même. Son rôle est de :
    # 1. Valider rigoureusement la requête et les permissions.
    # 2. Créer une entrée en base de données pour cette évaluation avec le statut "pending".
    # 3. Planifier l'exécution de la véritable fonction d'évaluation (`_do_evaluation`) en arrière-plan.
    # 4. Renvoyer immédiatement une réponse au client avec l'ID de l'évaluation,
    #    que le client pourra utiliser pour suivre l'avancement.

    # 1. Contrôles de sécurité et de propriété
    _assert_member(sess, team_id, current_user)
    assert_owner(sess, project_id, current_user, team_id)

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404, "Projet introuvable")

    # 2. Validation des IDs fournis dans la requête
    run = sess.get(ModelRun, payload.model_run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(400, "model_run_id invalide")

    cfg = sess.get(DataConfig, payload.data_config_id)
    if not cfg or cfg.train_dataset.project_id != project_id or cfg.test_dataset.project_id != project_id:
        raise HTTPException(400, "DataConfig invalide ou ne correspond pas à ce projet")

    # 3. Création de l'enregistrement de l'évaluation en BDD
    eval_run = EvaluationRun(
        project_id=project_id,
        model_run_id=payload.model_run_id,
        status="pending", # Le statut initial est "en attente"
    )
    sess.add(eval_run)
    sess.commit()
    sess.refresh(eval_run)

    # 4. Planification de la tâche de fond
    background_tasks.add_task(
        _do_evaluation, # La fonction qui sera exécutée en arrière-plan
        project_id,
        eval_run.id,
        payload.model_run_id,
        cfg.test_dataset_id,
        payload.data_config_id,
    )

    # La réponse est immédiate et contient l'ID pour le suivi.
    return {"eval_id": eval_run.id, "status": eval_run.status}


# ----------------- Fonction d'Exécution de l'Évaluation (Tâche de Fond) -----------------
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
    # BLOC DE LOGIQUE DE LA TÂCHE DE FOND (_do_evaluation)
    # C'est le cœur du système d'évaluation. Cette fonction est exécutée en arrière-plan
    # et n'est pas une route API. Son déroulement est le suivant :
    # 1.  Initialisation : Prépare une file (`queue`) pour les logs et met à jour le statut
    #     de l'évaluation en "running" dans la BDD.
    # 2.  Préparation : Récupère les chemins des artéfacts (modèle, dataset) et crée
    #     un fichier de configuration (`config_data.json`) à la volée.
    # 3.  Construction de la commande Docker : Assemble une commande `docker run` complexe
    #     qui monte les fichiers nécessaires en tant que volumes et lance le script `evaluate.py`
    #     de l'utilisateur dans un environnement isolé (pas de réseau, ressources limitées).
    # 4.  Exécution et Streaming des Logs : Lance la commande Docker via `subprocess.Popen`
    #     et capture la sortie (logs) ligne par ligne, en les poussant dans la file d'attente
    #     pour le streaming SSE.
    # 5.  Gestion des Résultats : Selon le code de sortie et la présence du fichier de
    #     métriques, met à jour le statut final ("succeeded" ou "failed")
    #     et persiste les métriques et les logs en BDD.
    # 6.  Mise à Jour du Projet : Met à jour un champ de résumé sur l'objet `AIProject`
    #     avec les métriques clés de cette évaluation.
    # 7.  Nettoyage : Retire la file de logs du dictionnaire global.

    # 1. Initialisation
    q = eval_log_channels.setdefault(eval_id, queue.SimpleQueue())
    all_logs: list[str] = []

    def push(msg: str) -> None:
        q.put(msg)
        all_logs.append(msg)

    with SessionLocal() as sess:
        er = sess.get(EvaluationRun, eval_id)
        er.started_at = datetime.utcnow()
        er.status = "running"
        sess.add(er)
        sess.commit()
    push(f"Evaluation {eval_id} started at {datetime.utcnow().isoformat()}")

    # 2. Préparation des ressources
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

    cfg_data = {"features": cfg.features, "sensitive_attrs": cfg.sensitive_attrs}
    cd_path = model_dir / "config_data.json"
    cd_path.write_text(js.dumps(cfg_data, indent=2), encoding="utf-8")
    push(f"Config data dumped → {cd_path.name}")

    # 3. Construction de la commande Docker
    output_dir = model_dir / "output"
    metrics_json = output_dir / "metrics.json"

    host_app_dir = Path(__file__).resolve().parents[2]
    cmd = [
        "docker", "run", "--rm", "--cpus=2.0", "--memory=4g", "--network=none",
        "--entrypoint", "/bin/sh",
        "-v", f"{to_docker_path(host_app_dir)}:/app",
        "-v", f"{to_docker_path(model_dir)}:/code",
        "-v", f"{to_docker_path(Path(ds.path))}:/data/test.csv",
        "-v", f"{to_docker_path(output_dir)}:/output",
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

    # 4. Exécution et capture des logs
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

    # 5. Gestion des résultats (échec)
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

    # 5. Gestion des résultats (succès)
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

    # 6. Mise à jour du résumé sur l'objet AIProject
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

    # 7. Nettoyage
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
    # BLOC LISTAGE DES ÉVALUATIONS
    # Route standard pour lister toutes les évaluations (passées et en cours)
    # d'un projet, après avoir vérifié que l'utilisateur est bien membre de l'équipe.
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
    # BLOC LECTURE D'UNE ÉVALUATION
    # Route standard pour récupérer les détails complets (statut, logs, métriques)
    # d'une seule évaluation par son ID.
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
    # BLOC RÉCUPÉRATION DES GRAPHIQUES
    # Permet de télécharger un fichier image (un graphique, ex: matrice de confusion)
    # qui a été généré par le script d'évaluation dans le conteneur Docker.
    # La logique consiste à retrouver le chemin de l'artéfact du modèle pour
    # en déduire le chemin du dossier `output` où les graphiques sont stockés.
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
    # BLOC DE STREAMING DES LOGS EN TEMPS RÉEL (SSE)
    # Cette route utilise les Server-Sent Events (SSE) pour "pousser" des données
    # du serveur vers le client. C'est la contrepartie de la `queue` de logs.
    # 1. Trouve la bonne file de logs dans le dictionnaire global `eval_log_channels`.
    # 2. Le `event_generator` est une boucle asynchrone qui attend des messages
    #    dans la file (`q.get`). Dès qu'un message arrive (poussé par `_do_evaluation`),
    #    il l'envoie au client.
    # 3. `EventSourceResponse` gère le protocole SSE pour cette communication temps réel.
    _assert_member(sess, team_id, current_user)

    q = eval_log_channels.get(eval_id)
    if q is None:
        raise HTTPException(404, "Évaluation inconnue ou non démarrée")

    loop = asyncio.get_running_loop()

    async def event_generator():
        while True:
            # S'arrête proprement si le client se déconnecte
            if await request.is_disconnected():
                break
            # Attend (sans bloquer le serveur) qu'un log soit disponible dans la file
            line = await loop.run_in_executor(None, q.get)
            # Envoie le log au client au format SSE
            yield {"data": line}

    return EventSourceResponse(event_generator())
