# app/tasks/cleanup.py
import os
import gzip
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from app.db import SessionLocal
from app.models import ModelRun, EvaluationRun, ModelArtifact

# ------- CONFIG ------------
# nombre de jours au-delà duquel on purge
RETENTION_DAYS = 7

# dossier parent de storage/models et storage/data
BASE_STORAGE = Path(__file__).resolve().parents[2] / "storage"


def purge_old_runs():
    """Supprime les ModelRun/EvaluationRun > RETENTION_DAYS et leurs artefacts."""
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    with SessionLocal() as sess:
        # 1) ModelRun
        runs = sess.exec(
            select(ModelRun).where(ModelRun.finished_at != None, ModelRun.finished_at < cutoff)
        ).all()
        for run in runs:
            # supprimer les artefacts sur le disque
            arts = sess.exec(select(ModelArtifact).where(ModelArtifact.model_run_id == run.id)).all()
            for art in arts:
                try:
                    os.remove(art.path)
                except OSError:
                    pass
                sess.delete(art)
            sess.delete(run)

        # 2) EvaluationRun
        evals = sess.exec(
            select(EvaluationRun).where(EvaluationRun.finished_at != None, EvaluationRun.finished_at < cutoff)
        ).all()
        for er in evals:
            # si des images ou metrics existent en storage
            # on suppose er.metrics contient éventuellement des chemins
            m = er.metrics or {}
            for sub in m.get("explainability", {}).values():
                try:
                    os.remove(sub)
                except Exception:
                    pass
            sess.delete(er)

        sess.commit()


def prune_docker_containers():
    """Supprime les conteneurs Docker arrétés (orphelins)."""
    try:
        subprocess.run(
            ["docker", "container", "prune", "--force"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception:
        pass


def compress_old_logs():
    """Compresse en .gz les logs (ModelRun.logs, EvaluationRun.logs) plus anciens que RETENTION_DAYS."""
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    with SessionLocal() as sess:
        # on ne charge pas tout, seulement ceux qui ne sont pas encore compressés
        runs = sess.exec(
            select(ModelRun).where(
                ModelRun.finished_at != None,
                ModelRun.finished_at < cutoff,
                ModelRun.logs != None,
            )
        ).all()
        for run in runs:
            # si déjà compressé, on skip (on peut ajouter un flag ou détecter .gz quelque part)
            log_path = BASE_STORAGE / "logs" / f"run_{run.id}.log"
            if log_path.exists():
                gz_path = log_path.with_suffix(".log.gz")
                with log_path.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                log_path.unlink()

        # même pour EvaluationRun si tu stockes les logs en fichier
        # à adapter si tu les stockes dans la base seulement

        sess.commit()


def start_scheduler():
    sched = BackgroundScheduler(timezone="UTC")
    # purge quotidienne à 2h00 UTC
    sched.add_job(purge_old_runs,    "cron", hour=2, minute=0, id="purge_runs")
    sched.add_job(prune_docker_containers, "cron", hour=3, minute=0, id="prune_docker")
    sched.add_job(compress_old_logs, "cron", hour=4, minute=0, id="compress_logs")
    sched.start()
