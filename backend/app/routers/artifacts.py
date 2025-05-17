# app/routers/artifacts.py
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select

# ─── modèles / auth / helpers ───────────────────────────────────────────────
from app.models import ModelArtifact
from app.auth import User, get_current_user
from app.utils.dependencies import assert_owner,get_session

# ────────────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/projects/{project_id}/artifacts",
    tags=["artifacts"],
    responses={404: {"description": "Not found"}},
)

# ---------------------------------------------------------------------------
# Liste des artefacts pour un projet
# ---------------------------------------------------------------------------

@router.get("", response_model=List[ModelArtifact], summary="Liste les artefacts du projet")
def list_artifacts(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)
    return sess.exec(
        select(ModelArtifact).where(ModelArtifact.project_id == project_id)
    ).all()


# ---------------------------------------------------------------------------
# Téléchargement d'un artefact précis
# ---------------------------------------------------------------------------

@router.get("/{artifact_id}", response_class=FileResponse, summary="Télécharge l'artefact")
def download_artifact(
    project_id: int,
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    assert_owner(sess, project_id, current_user)

    art = sess.get(ModelArtifact, artifact_id)
    if not art or art.project_id != project_id:
        raise HTTPException(404, "Artefact introuvable")

    file_path = Path(art.path)
    if not file_path.exists():
        raise HTTPException(404, "Fichier non trouvé sur le disque")

    file_path = file_path.resolve()
    base_dir = Path(__file__).resolve().parents[2] / "storage" / "models" / f"project_{project_id}"
    if base_dir not in file_path.parents:
        raise HTTPException(403, "Accès interdit")

    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )
