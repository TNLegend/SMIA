from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.db import SessionLocal
from app.models import AIProject, AIProjectCreate, AIProjectRead
from app.auth import get_current_user, User

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/",
    response_model=AIProjectRead,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    payload: AIProjectCreate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        proj = AIProject.from_orm(payload)
        # classification statique pour l'instant
        proj.risk_level = "medium"
        sess.add(proj)
        sess.commit()
        sess.refresh(proj)
        return proj


@router.get(
    "/",
    response_model=List[AIProjectRead]
)
def list_projects(current_user: User = Depends(get_current_user)):
    with SessionLocal() as sess:
        return sess.exec(select(AIProject)).all()


@router.get(
    "/{project_id}",
    response_model=AIProjectRead
)
def read_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        proj = sess.get(AIProject, project_id)
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        return proj


@router.put(
    "/{project_id}",
    response_model=AIProjectRead
)
def update_project(
    project_id: int,
    payload: AIProjectCreate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        proj = sess.get(AIProject, project_id)
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        proj.name = payload.name
        proj.description = payload.description
        proj.status = payload.status
        proj.objectives = payload.objectives
        proj.stakeholders = payload.stakeholders
        proj.updated_at = datetime.utcnow()
        # on recalculera le risk_level en Sprint 3
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
):
    with SessionLocal() as sess:
        proj = sess.get(AIProject, project_id)
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        sess.delete(proj)
        sess.commit()
    return None
