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
from sqlalchemy.orm import selectinload
# ─── Response Schemas ────────────────────────────────────
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import selectinload
class TeamRead(SQLModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class MembershipRead(SQLModel):
    user_id: int
    team_id: int
    role: str
    invited_at: datetime
    accepted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    user: UserRead
    team: TeamRead
    class Config:
        orm_mode = True
        from_attributes = True

# ─── Router ─────────────────────────────────────────────
router = APIRouter(prefix="/teams", tags=["teams"])


@router.post(
    "/",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED
)
def create_team(
    name: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
):
    db: Session = SessionLocal()
    try:
        # ensure unique
        if db.exec(select(Team).where(Team.name == name)).first():
            raise HTTPException(400, "Team name already exists")

        team = Team(name=name, owner_id=current_user.id)
        db.add(team)
        db.commit()
        db.refresh(team)

        # auto-add owner membership
        membership = TeamMembership(
            user_id=current_user.id,
            team_id=team.id,
            role="owner",
            invited_at=datetime.utcnow(),
            accepted_at=datetime.utcnow(),
        )
        db.add(membership)
        db.commit()

        return TeamRead.from_orm(team)
    finally:
        db.close()


@router.get(
    "/",
    response_model=List[TeamRead]
)
def list_teams(
    current_user: User = Depends(get_current_user),
):
    db: Session = SessionLocal()
    try:
        rows = db.exec(
            select(TeamMembership).where(
                TeamMembership.user_id == current_user.id,
                TeamMembership.accepted_at.is_not(None)
            )
        ).all()
        teams = [db.get(Team, m.team_id) for m in rows]
        return teams
    finally:
        db.close()

@router.get(
    "/invitations",
    response_model=list[MembershipRead],
    summary="Liste mes invitations en attente"
)
def list_my_invitations(current_user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        rows = db.exec(
            select(TeamMembership)
            .where(
            TeamMembership.user_id == current_user.id,
            TeamMembership.accepted_at.is_(None),
            TeamMembership.revoked_at.is_(None),
            )
            # on charge en même temps user et team
            .options(
            selectinload(TeamMembership.user),
            selectinload(TeamMembership.team),
            )
            ).all()

        return [MembershipRead.from_orm(m) for m in rows]
    finally:
        db.close()


@router.get(
    "/{team_id}",
    response_model=TeamRead
)
def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
):
    db: Session = SessionLocal()
    try:
        team = db.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Team not found")

        # ensure membership
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


@router.get(
    "/{team_id}/members",
    response_model=List[MembershipRead],
    summary="Liste les membres d'une équipe"
)
def list_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
):
    db: Session = SessionLocal()
    try:
        # must be member to list
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
            # pareil : on veut le user.username au lieu de l’id brut
            .options(selectinload(TeamMembership.user))
            ).all()
        return [MembershipRead.from_orm(m) for m in rows]
    finally:
        db.close()


@router.post(
    "/{team_id}/members",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Inviter un utilisateur à rejoindre l’équipe"
)
def invite_member(
    team_id: int,
    username: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
):
    db: Session = SessionLocal()
    try:
        team = db.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Team not found")

        # only owner or manager can invite
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

        if db.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == user.id
            )
        ).first():
            raise HTTPException(400, "Already invited or member")

        invite = TeamMembership(
            user_id=user.id,
            team_id=team_id,
            role="member",
            invited_at=datetime.utcnow(),
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return MembershipRead.from_orm(invite)
    finally:
        db.close()


@router.put(
    "/{team_id}/members/me/accept",
    response_model=MembershipRead,
    status_code=status.HTTP_200_OK,
    summary="Accepter une invitation"
)
def accept_invite(
    team_id: int,
    current_user: User = Depends(get_current_user),
):
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

@router.delete("/{team_id}/members/me", status_code=204,
               summary="Refuser mon invitation")
def refuse_my_invite(team_id: int, current_user: User = Depends(get_current_user)):
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


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirer un membre de l’équipe"
)
def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    db: Session = SessionLocal()
    try:
        # check team exists
        if not db.get(Team, team_id):
            raise HTTPException(404, "Team not found")

        # only owner or manager can remove
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


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer l’équipe"
)
def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
):
    db: Session = SessionLocal()
    try:
        team = db.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Team not found")
        if team.owner_id != current_user.id:
            raise HTTPException(403, "Only the owner can delete the team")

        # Supprimer les non conformités des checklist items de tous les projets liés à l'équipe
        for project in team.projects:
            for checklist_item in project.checklist_items:
                for nc in checklist_item.non_conformites:
                    db.delete(nc)
                db.delete(checklist_item)
            db.delete(project)

        # Supprimer les membres et documents (cascade déjà configurée)
        for membership in team.members:
            db.delete(membership)
        for doc in team.documents:
            db.delete(doc)

        # Enfin supprimer l’équipe
        db.delete(team)
        db.commit()
    finally:
        db.close()

