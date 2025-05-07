# app/routers/projects.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import SessionLocal
from app.models import AIProject, AIProjectCreate, AIProjectRead
from app.auth import get_current_user, User

router = APIRouter(prefix="/projects", tags=["projects"])

def get_session():
    with SessionLocal() as sess:
        yield sess

@router.post(
    "/",
    response_model=AIProjectRead,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    payload: AIProjectCreate,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = AIProject.from_orm(payload)
    # you could override owner here:
    proj.owner = current_user.username
    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return proj

@router.get(
    "/",
    response_model=List[AIProjectRead]
)
def list_projects(
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    return sess.exec(select(AIProject)).all()

@router.get(
    "/{project_id}",
    response_model=AIProjectRead
)
def read_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return proj

@router.put(
    "/{project_id}",
    response_model=AIProjectRead
)
def update_project(
    project_id: int,
    payload: AIProjectCreate,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # copy all updatable fields
    update_data = payload.dict(exclude_unset=True)
    for key, val in update_data.items():
        setattr(proj, key, val)
    proj.updated_at = datetime.utcnow()

    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return proj

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    sess.delete(proj)
    sess.commit()
    return
