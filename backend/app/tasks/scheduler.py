from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.db import SessionLocal
from app.models import NonConformite, AIProject
import logging
from app.models import Notification
logger = logging.getLogger(__name__)




def check_nc_alerts():
    with SessionLocal() as sess:
        now = datetime.utcnow()
        seuil = now + timedelta(days=7)

        nc_critique = sess.exec(
            select(NonConformite)
            .where(
                NonConformite.type_nc == "majeure",
                NonConformite.statut != "corrigee",
                NonConformite.deadline_correction <= seuil,
            )
        ).all()

        for nc in nc_critique:
            # Vérifie si notification existe déjà et non lue
            existing = sess.exec(
                select(Notification)
                .where(
                    Notification.nonconformite_id == nc.id,
                    Notification.read == False,
                )
            ).first()
            if existing:
                continue

            item = nc.checklist_item  # accès direct à l’item parent
            message = (
                    f"NC majeure {item.control_id}-Q{nc.question_index + 1} – "
                    f"deadline "
                    f"{nc.deadline_correction.strftime('%Y-%m-%d') if nc.deadline_correction else 'inconnue'}"
                    )
            notification = Notification(
                team_id=nc.checklist_item.project.team_id,
                project_id=nc.checklist_item.project_id,
                nonconformite_id=nc.id,
                message=message,
            )
            sess.add(notification)

        sess.commit()


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Tâche qui tourne tous les jours à 2h du matin (exemple)
    #trigger = CronTrigger(hour=2, minute=0)
    trigger = CronTrigger(minute="*/1")

    scheduler.add_job(check_nc_alerts, trigger, id="check_nc_alerts", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler APScheduler démarré avec la tâche check_nc_alerts")
