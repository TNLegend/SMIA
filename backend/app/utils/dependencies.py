# utils/dependencies.py
from typing import Generator
from fastapi import HTTPException
from sqlmodel import Session
from app.db import SessionLocal
from app.models import AIProject, User

def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as sess:
        yield sess

def assert_owner(sess: Session, project_id: int, user: User):
    proj = sess.get(AIProject, project_id)
    if not proj or proj.owner != user.username:
        raise HTTPException(403, "Accès interdit")
