from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from datetime import datetime
from typing import List

from app.auth import get_current_user, User
from app.models import Notification, TeamMembership
from app.utils.dependencies import get_session
from sqlmodel import Session

router = APIRouter(prefix="/teams/{team_id}/notifications", tags=["notifications"])

@router.get("/", response_model=List[Notification])
def list_team_notifications(
    team_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # Vérifier appartenance à l'équipe
    mem = sess.exec(
        select(TeamMembership)
        .where(TeamMembership.team_id == team_id,
               TeamMembership.user_id == current_user.id,
               TeamMembership.accepted_at.is_not(None))
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Accès interdit")

    # Ne renvoyer que les non-lues (ou toutes si tu veux)
    notifs = sess.exec(
        select(Notification)
        .where(Notification.team_id == team_id,
               Notification.read == False)
        .order_by(Notification.created_at.desc())
    ).all()
    return notifs

@router.put("/{notif_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(
    team_id: int,
    notif_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # même contrôle d’accès…
    notif = sess.get(Notification, notif_id)
    if not notif or notif.team_id != team_id:
        raise HTTPException(404, detail="Notification introuvable")
    notif.read = True
    notif.updated_at = datetime.utcnow()
    sess.add(notif)
    sess.commit()
