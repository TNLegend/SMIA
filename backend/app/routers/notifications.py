from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from datetime import datetime
from typing import List

from app.auth import get_current_user, User
from app.models import Notification, TeamMembership
from app.utils.dependencies import get_session
from sqlmodel import Session

# BLOC D'INITIALISATION DU ROUTER
# Toutes les routes de ce fichier seront préfixées par `/teams/{team_id}/notifications`
# et taguées comme "notifications" dans la documentation de l'API.
router = APIRouter(prefix="/teams/{team_id}/notifications", tags=["notifications"])


@router.get("/", response_model=List[Notification])
def list_team_notifications(
        team_id: int,
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # BLOC DE LISTAGE DES NOTIFICATIONS
    # Cette route récupère la liste des notifications pour une équipe donnée.
    # 1.  Vérifie que l'utilisateur courant est bien un membre actif de l'équipe
    #     pour des raisons de sécurité.
    # 2.  Récupère toutes les notifications de l'équipe qui ne sont pas encore lues (`read == False`).
    # 3.  Les trie par date de création, de la plus récente à la plus ancienne.

    # Vérifier appartenance à l'équipe
    mem = sess.exec(
        select(TeamMembership)
        .where(TeamMembership.team_id == team_id,
               TeamMembership.user_id == current_user.id,
               TeamMembership.accepted_at.is_not(None))
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Accès interdit")

    # Ne renvoyer que les non-lues
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
    # BLOC POUR MARQUER UNE NOTIFICATION COMME LUE
    # Cette route met à jour le statut d'une notification pour la marquer comme lue.
    # Bien qu'un contrôle d'accès complet de l'utilisateur ne soit pas présent ici,
    # elle vérifie que la notification demandée appartient bien à l'équipe spécifiée dans l'URL.
    # 1.  Récupère la notification par son ID.
    # 2.  Vérifie qu'elle existe et qu'elle appartient à la bonne équipe.
    # 3.  Passe son champ `read` à `True` et met à jour son `updated_at`.
    # 4.  Retourne un statut 204 (No Content), pratique standard pour une action
    #     réussie qui ne nécessite pas de corps de réponse.

    # Le contrôle d'accès de l'utilisateur à l'équipe devrait être ajouté ici pour la cohérence.
    notif = sess.get(Notification, notif_id)
    if not notif or notif.team_id != team_id:
        raise HTTPException(404, detail="Notification introuvable")

    notif.read = True
    notif.updated_at = datetime.utcnow()
    sess.add(notif)
    sess.commit()