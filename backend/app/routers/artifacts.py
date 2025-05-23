# app/routers/artifacts.py
from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.auth import User, get_current_user
from app.models import AIProject, ModelArtifact, TeamMembership
from app.utils.dependencies import get_session

# ───────────────────────── helpers ──────────────────────────────────────────
def _assert_member(sess: Session, team_id: int, user: User) -> None:
    """403 si *user* n’est pas membre (invitation acceptée) de l’équipe."""
    mem = sess.exec(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not mem:
        raise HTTPException(403, "Accès interdit à cette équipe")

# ───────────────────────── Router ───────────────────────────────────────────
router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/artifacts",
    tags=["artifacts"],
    responses={404: {"description": "Not found"}},
)

# ═════════════════════ Lister les artefacts ════════════════════════════════
@router.get("", response_model=List[ModelArtifact])
def list_artifacts(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404, "Projet introuvable")

    return sess.exec(
        select(ModelArtifact).where(ModelArtifact.project_id == project_id)
    ).all()

# ═════════════════════ Télécharger un artefact ═════════════════════════════
@router.get("/{artifact_id}", response_class=FileResponse)
def download_artifact(
    team_id: int,
    project_id: int,
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    _assert_member(sess, team_id, current_user)

    art = sess.get(ModelArtifact, artifact_id)
    if not art or art.project_id != project_id:
        raise HTTPException(404, "Artefact introuvable")

    file_path = Path(art.path)
    if not file_path.exists():
        raise HTTPException(404, "Fichier non trouvé sur le disque")

    # Sécurise : le fichier doit rester dans storage/models/project_{id}
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "storage"
        / "models"
        / f"project_{project_id}"
    )
    if base_dir not in file_path.resolve().parents:
        raise HTTPException(403, "Accès interdit")

    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )
