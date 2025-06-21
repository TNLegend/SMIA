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
    # BLOC DE VÉRIFICATION D'APPARTENANCE
    # Cette fonction sert de garde de sécurité. Elle vérifie si l'utilisateur
    # courant est bien un membre dont l'invitation à l'équipe a été acceptée.
    # Si la recherche en base de données ne retourne aucun résultat,
    # une erreur 403 (Accès Interdit) est levée, stoppant l'exécution.
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

# BLOC DE CONFIGURATION DU ROUTER
# Ici, on initialise un "router" FastAPI. Toutes les routes définies dans ce
# fichier auront une URL qui commence par "/teams/{team_id}/projects/{project_id}/artifacts"
# et seront regroupées sous le tag "artifacts" dans la documentation de l'API.
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
    # BLOC DE LOGIQUE POUR LISTER LES ARTEFACTS
    # 1. Sécurité : On vérifie d'abord que l'utilisateur a le droit d'accéder à l'équipe.
    _assert_member(sess, team_id, current_user)

    # 2. Validation : On s'assure que le projet demandé existe et qu'il appartient bien
    #    à l'équipe spécifiée dans l'URL. C'est pour éviter qu'un utilisateur n'accède
    #    à un projet via une URL d'une autre équipe.
    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(404, "Projet introuvable")

    # 3. Action : Si tout est en règle, on retourne la liste de tous les artefacts
    #    associés à ce projet.
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
    # BLOC DE LOGIQUE POUR TÉLÉCHARGER UN ARTEFACT
    # 1. Sécurité et Validation : Comme pour la liste, on vérifie l'appartenance
    #    à l'équipe, puis on s'assure que l'artefact demandé existe et qu'il
    #    appartient bien au bon projet.
    _assert_member(sess, team_id, current_user)
    art = sess.get(ModelArtifact, artifact_id)
    if not art or art.project_id != project_id:
        raise HTTPException(404, "Artefact introuvable")

    # 2. Vérification du fichier : On contrôle que le chemin du fichier (stocké en BDD)
    #    existe bien sur le disque du serveur.
    file_path = Path(art.path)
    if not file_path.exists():
        raise HTTPException(404, "Fichier non trouvé sur le disque")

    # 3. Sécurité Fichier : C'est une vérification cruciale contre les attaques de
    #    type "Path Traversal". On s'assure que le chemin du fichier demandé se
    #    trouve bien dans le dossier de stockage attendu pour ce projet. Cela empêche
    #    de télécharger des fichiers système sensibles.
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "storage"
        / "models"
        / f"project_{project_id}"
    )
    if base_dir not in file_path.resolve().parents:
        raise HTTPException(403, "Accès interdit")

    # 4. Action : Si toutes les vérifications passent, on retourne le fichier
    #    en utilisant FileResponse, ce qui permet un téléchargement efficace.
    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )