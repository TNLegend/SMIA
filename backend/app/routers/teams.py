# app/routers/teams.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from fastapi import Body
from app.db import SessionLocal
from app.models import Team, TeamMembership, User
# on importe aussi le schéma de lecture UserRead
from app.models import UserRead
from app.auth import get_current_user  # correct import
# `selectinload` est utilisé pour optimiser les requêtes en chargeant
# les relations en même temps (eager loading).
from sqlalchemy.orm import selectinload

# ─── Schémas de Réponse (Response Schemas) ────────────────────────────────────
# BLOC DE DÉFINITION DES SCHÉMAS DE RÉPONSE
# Ces classes Pydantic/SQLModel définissent la structure des données qui seront
# renvoyées au client. Elles permettent de s'assurer que seules les informations
# pertinentes sont exposées et que le format est correct.
from sqlmodel import SQLModel, Field

class TeamRead(SQLModel):
    """Schéma pour la lecture des informations de base d'une équipe."""
    id: int
    name: str
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class MembershipRead(SQLModel):
    """Schéma pour la lecture des informations sur l'appartenance d'un utilisateur à une équipe.
    Il inclut les détails de l'utilisateur (`user`) et de l'équipe (`team`) pour une réponse plus riche."""
    user_id: int
    team_id: int
    role: str
    invited_at: datetime
    accepted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    user: UserRead # Relation imbriquée pour obtenir les infos de l'utilisateur
    team: TeamRead # Relation imbriquée pour obtenir les infos de l'équipe
    class Config:
        from_attributes = True

# ─── Router ─────────────────────────────────────────────
router = APIRouter(prefix="/teams", tags=["teams"])

# ═════════════════════ Création et Consultation des Équipes ════════════════════════════

@router.post("/", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    name: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
):
    # BLOC DE CRÉATION D'ÉQUIPE
    # Cette route gère la création d'une nouvelle équipe.
    # 1.  Vérifie que le nom de l'équipe n'est pas déjà utilisé.
    # 2.  Crée l'équipe en base de données avec l'utilisateur courant comme propriétaire.
    # 3.  Crée automatiquement une entrée `TeamMembership` pour le propriétaire,
    #     le marquant comme membre "owner" et accepté immédiatement.
    db: Session = SessionLocal()
    try:
        if db.exec(select(Team).where(Team.name == name)).first():
            raise HTTPException(400, "Team name already exists")

        team = Team(name=name, owner_id=current_user.id)
        db.add(team)
        db.commit()
        db.refresh(team)

        membership = TeamMembership(
            user_id=current_user.id, team_id=team.id, role="owner",
            invited_at=datetime.utcnow(), accepted_at=datetime.utcnow(),
        )
        db.add(membership)
        db.commit()

        return TeamRead.from_orm(team)
    finally:
        db.close()

@router.get("/", response_model=List[TeamRead])
def list_teams(current_user: User = Depends(get_current_user)):
    # BLOC LISTAGE DES ÉQUIPES DE L'UTILISATEUR
    # Retourne la liste de toutes les équipes dont l'utilisateur courant est un membre actif.
    db: Session = SessionLocal()
    try:
        rows = db.exec(
            select(TeamMembership).where(
                TeamMembership.user_id == current_user.id,
                TeamMembership.accepted_at.is_not(None)
            )
        ).all()
        # Récupère les objets Team complets à partir des memberships
        teams = [db.get(Team, m.team_id) for m in rows]
        return teams
    finally:
        db.close()

@router.get("/{team_id}", response_model=TeamRead)
def get_team(team_id: int, current_user: User = Depends(get_current_user)):
    # BLOC LECTURE D'UNE ÉQUIPE SPÉCIFIQUE
    # Récupère les informations d'une seule équipe, après avoir vérifié que
    # l'utilisateur courant en est bien membre.
    db: Session = SessionLocal()
    try:
        team = db.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Team not found")
        mem = db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == current_user.id,
                TeamMembership.accepted_at.is_not(None)
            )
        ).first()
        if not mem:
            raise HTTPException(403, "Not a member of this team")
        return team
    finally:
        db.close()

# ═════════════════════ Gestion des Membres et Invitations ════════════════════════════

@router.get("/invitations", response_model=list[MembershipRead], summary="Liste mes invitations en attente")
def list_my_invitations(current_user: User = Depends(get_current_user)):
    # BLOC LISTAGE DES INVITATIONS EN ATTENTE
    # Route dédiée pour que l'utilisateur puisse voir les invitations d'équipes qu'il n'a pas encore acceptées.
    db: Session = SessionLocal()
    try:
        rows = db.exec(
            select(TeamMembership).where(
                TeamMembership.user_id == current_user.id,
                TeamMembership.accepted_at.is_(None), # Invitation non acceptée
                TeamMembership.revoked_at.is_(None),  # Invitation non révoquée
            )
            # `selectinload` est une optimisation qui pré-charge les données des tables
            # liées (`user` et `team`) en une seule requête, évitant le problème "N+1 queries".
            .options(
                selectinload(TeamMembership.user),
                selectinload(TeamMembership.team),
            )
        ).all()
        return [MembershipRead.from_orm(m) for m in rows]
    finally:
        db.close()

@router.get("/{team_id}/members", response_model=List[MembershipRead], summary="Liste les membres d'une équipe")
def list_members(team_id: int, current_user: User = Depends(get_current_user)):
    # BLOC LISTAGE DES MEMBRES D'UNE ÉQUIPE
    # Permet de voir tous les membres actifs d'une équipe spécifique.
    # 1.  Vérifie d'abord que l'utilisateur qui fait la demande est lui-même membre de l'équipe.
    # 2.  Si c'est le cas, récupère la liste de tous les membres acceptés.
    # 3.  Utilise `selectinload` pour charger efficacement les détails de chaque utilisateur.
    db: Session = SessionLocal()
    try:
        mem = db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == current_user.id,
                TeamMembership.accepted_at.is_not(None)
            )
        ).first()
        if not mem:
            raise HTTPException(403, "Not authorized")

        rows = db.exec(
            select(TeamMembership)
            .where(
                TeamMembership.team_id == team_id,
                TeamMembership.accepted_at.is_not(None)
            )
            .options(selectinload(TeamMembership.user))
        ).all()
        return [MembershipRead.from_orm(m) for m in rows]
    finally:
        db.close()

# ═════════════════════ Actions sur les Membres (Invitation, Acceptation, Suppression) ════════════════════════════

@router.post("/{team_id}/members", response_model=MembershipRead, status_code=status.HTTP_201_CREATED, summary="Inviter un utilisateur à rejoindre l’équipe")
def invite_member(
    team_id: int,
    username: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
):
    # BLOC POUR INVITER UN MEMBRE
    # Cette route permet à un propriétaire ou manager d'inviter un nouvel utilisateur.
    # 1.  Vérifie que l'utilisateur qui invite a les droits suffisants ("owner" ou "manager").
    # 2.  Vérifie que l'utilisateur invité existe dans le système.
    # 3.  S'assure que l'utilisateur n'est pas déjà membre ou n'a pas déjà une invitation.
    # 4.  Crée une nouvelle entrée `TeamMembership` avec `accepted_at` à `None`, ce qui
    #     matérialise une invitation en attente.
    db: Session = SessionLocal()
    try:
        team = db.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Team not found")

        mymem = db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == current_user.id
            )
        ).first()
        if not mymem or mymem.role not in ("owner", "manager"):
            raise HTTPException(403, "Not authorized to invite")

        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(404, "User not found")

        if db.exec(select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == user.id)).first():
            raise HTTPException(400, "Already invited or member")

        invite = TeamMembership(
            user_id=user.id, team_id=team_id, role="member", invited_at=datetime.utcnow(),
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return MembershipRead.from_orm(invite)
    finally:
        db.close()

@router.put("/{team_id}/members/me/accept", response_model=MembershipRead, status_code=status.HTTP_200_OK, summary="Accepter une invitation")
def accept_invite(team_id: int, current_user: User = Depends(get_current_user)):
    # BLOC POUR ACCEPTER UNE INVITATION
    # Permet à l'utilisateur courant (`me`) d'accepter une invitation en attente pour une équipe.
    # Elle trouve l'invitation correspondante et met à jour le champ `accepted_at`
    # avec la date et l'heure actuelles, ce qui finalise l'adhésion.
    db: Session = SessionLocal()
    try:
        mem = db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == current_user.id
            )
        ).first()
        if not mem:
            raise HTTPException(404, "No invitation found")
        if mem.accepted_at:
            raise HTTPException(400, "Already accepted")

        mem.accepted_at = datetime.utcnow()
        db.add(mem)
        db.commit()
        db.refresh(mem)
        return MembershipRead.from_orm(mem)
    finally:
        db.close()

@router.delete("/{team_id}/members/me", status_code=204, summary="Refuser mon invitation")
def refuse_my_invite(team_id: int, current_user: User = Depends(get_current_user)):
    # BLOC POUR REFUSER UNE INVITATION
    # Permet à l'utilisateur courant de refuser une invitation.
    # L'enregistrement de l'invitation (`TeamMembership`) est simplement supprimé de la base de données.
    db = SessionLocal()
    try:
        mem = db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == current_user.id,
                TeamMembership.accepted_at.is_(None),
            )
        ).first()
        if not mem:
            raise HTTPException(404, "Invitation introuvable")
        db.delete(mem)
        db.commit()
    finally:
        db.close()

@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Retirer un membre de l’équipe")
def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    # BLOC POUR RETIRER UN MEMBRE
    # Permet à un propriétaire ou manager de retirer un autre utilisateur de l'équipe.
    # La logique est similaire à celle du refus d'invitation : l'enregistrement `TeamMembership`
    # de l'utilisateur cible est supprimé.
    db: Session = SessionLocal()
    try:
        if not db.get(Team, team_id):
            raise HTTPException(404, "Team not found")

        mymem = db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == current_user.id
            )
        ).first()
        if not mymem or mymem.role not in ("owner", "manager"):
            raise HTTPException(403, "Not authorized to remove members")

        mem = db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == user_id
            )
        ).first()
        if not mem:
            raise HTTPException(404, "Member not found")

        db.delete(mem)
        db.commit()
    finally:
        db.close()


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer l’équipe")
def delete_team(team_id: int, current_user: User = Depends(get_current_user)):
    # BLOC DE SUPPRESSION D'ÉQUIPE (OPÉRATION DESTRUCTIVE)
    # Cette route critique permet de supprimer une équipe entière et toutes ses données associées.
    # 1.  Le droit de suppression est strictement réservé au propriétaire de l'équipe (`owner_id`).
    # 2.  Elle effectue une "suppression en cascade" manuelle et explicite pour garantir
    #     qu'aucune donnée orpheline ne subsiste :
    #     - Supprime les non-conformités, puis les checklist_items, puis les projets.
    #     - Supprime toutes les appartenances (`memberships`) et les documents de l'équipe.
    # 3.  Enfin, après que toutes les dépendances ont été nettoyées, l'équipe elle-même est supprimée.
    db: Session = SessionLocal()
    try:
        team = db.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Team not found")
        if team.owner_id != current_user.id:
            raise HTTPException(403, "Only the owner can delete the team")

        for project in team.projects:
            for checklist_item in project.checklist_items:
                for nc in checklist_item.non_conformites:
                    db.delete(nc)
                db.delete(checklist_item)
            db.delete(project)

        for membership in team.members:
            db.delete(membership)
        for doc in team.documents:
            db.delete(doc)

        db.delete(team)
        db.commit()
    finally:
        db.close()

