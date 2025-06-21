# utils/dependencies.py
from typing import Generator
from fastapi import HTTPException, Depends
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db import SessionLocal
from app.models import AIProject, User, TeamMembership


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as sess:
        yield sess

def assert_owner(sess: Session, project_id: int, user: User,team_id: int):

    # only owner or manager can upload
    mymem = sess.exec(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id
        )
    ).first()
    if not mymem or mymem.role not in ("owner", "manager"):
        raise HTTPException(403, "Seul le propriétaire de l'equipe peut faire ca ")

