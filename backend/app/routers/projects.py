# app/routers/projects.py
from datetime import datetime, timedelta
from pathlib import Path as FSPath
from typing import List, Optional, Dict, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Body,
    UploadFile,
    File,
    Path,
    Form,
)
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select, delete

from app.auth import get_current_user, User
from app.db import SessionLocal
from app.models import (
    AIProject,
    AIProjectCreate,
    AIProjectRead,
    Comment,
    CommentCreate,
    ISO42001ChecklistItem,
    ActionCorrective,
    Proof, DataSet, ModelRun, TeamMembership,
    NonConformite,
    NonConformiteCreate,
    NonConformiteRead,
    NonConformiteUpdate, StatutNonConformite, TeamMemberResponse, Team,
)
from config.iso42001_requirements import ISO42001_REQUIREMENTS
from app.utils.dependencies import get_session
from app.utils.files import purge_project_storage
from sqlalchemy.orm import selectinload  # pour charger les enfants en une requête

# BLOC D'INITIALISATION DU ROUTER
# Le router est configuré pour toutes les routes liées aux projets au sein d'une équipe.
router = APIRouter(prefix="/teams/{team_id}/projects", tags=["projects"])


# --------Helper de Sécurité---------
# BLOC DE LA FONCTION D'AIDE (HELPER)
# Cette fonction est un garde de sécurité qui centralise les vérifications d'accès
# pour les opérations sur les sous-éléments d'un projet (comme un item de checklist).
def verify_access(
        team_id: int,
        project_id: int,
        item_id: int,
        current_user: User,
        sess: Session,
) -> ISO42001ChecklistItem:
    # 1. Vérifie que l'utilisateur est un membre actif de l'équipe.
    mem = sess.exec(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == current_user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Accès interdit à cette équipe")

    # 2. Vérifie que le projet appartient bien à l'équipe spécifiée.
    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Project not found")

    # 3. Vérifie que l'item (ex: de checklist) appartient bien au projet.
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    return item


# ─────────────────────────── CRUD des Projets ────────────────────────────────────
# BLOC DE GESTION DE LA CRÉATION ET LECTURE DES PROJETS

@router.post("/", response_model=AIProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
        team_id: int,
        payload: AIProjectCreate,
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # Route pour créer un nouveau projet d'IA.
    # 1.  Vérifie que l'utilisateur est bien membre de l'équipe dans laquelle il essaie de créer le projet.
    # 2.  Crée l'instance du projet en s'assurant que le `team_id` de l'URL est bien celui qui est utilisé.
    # 3.  Définit l'utilisateur courant comme propriétaire (`owner`) du projet.
    mem = sess.exec(
        select(TeamMembership)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == current_user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Accès interdit à cette équipe")

    proj = AIProject(**payload.dict(), team_id=team_id)
    proj.owner = current_user.username
    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return proj


@router.get("/", response_model=List[AIProjectRead])
def list_projects(
        team_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(6, gt=0, le=100),
        status: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # Route complexe pour lister les projets avec recherche, filtrage et pagination.
    # 1.  Vérifie l'appartenance de l'utilisateur à l'équipe.
    # 2.  Construit dynamiquement la requête SQLModel en ajoutant des clauses `where`
    #     si les filtres `status` ou `search` sont fournis.
    # 3.  Utilise `selectinload` pour charger en une seule fois les données liées
    #     (équipe -> membres -> utilisateurs), ce qui évite de multiples requêtes à la BDD (problème N+1).
    # 4.  Applique la pagination (`offset`, `limit`).
    # 5.  Construit manuellement la réponse pour y injecter la liste des membres (`team_members`)
    #     dans chaque projet, car ce champ n'est pas directement dans le modèle de BDD `AIProject`.

    membership = sess.exec(
        select(TeamMembership)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == current_user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    query = select(AIProject).where(AIProject.team_id == team_id)
    if status:
        query = query.where(AIProject.status == status)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            (AIProject.title.ilike(pattern))
            | (AIProject.description.ilike(pattern))
            | (AIProject.category.ilike(pattern))
            | (AIProject.owner.ilike(pattern))
        )

    query = query.options(
        selectinload(AIProject.team)
        .selectinload(Team.members)
        .selectinload(TeamMembership.user)
    )

    projects = sess.exec(query.offset(skip).limit(limit)).all()

    results = []
    for proj in projects:
        members_list = []
        if proj.team:
            for mem in proj.team.members:
                if mem.accepted_at is not None and mem.revoked_at is None:
                    members_list.append(
                        TeamMemberResponse(
                            name=mem.user.username,
                            role=mem.role,
                            avatar=None
                        )
                    )
        proj_dict = proj.dict()
        proj_dict["team_members"] = members_list
        results.append(proj_dict)

    return [AIProjectRead.parse_obj(p) for p in results]


from sqlalchemy.orm import selectinload


@router.get("/{project_id}", response_model=AIProjectRead)
def read_project(
        team_id: int,
        project_id: int,
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # BLOC DE LECTURE D'UN PROJET INDIVIDUEL
    # Cette route récupère les détails d'un projet spécifique.
    # 1.  Vérifie que l'utilisateur est bien membre de l'équipe.
    # 2.  Récupère le projet et valide son appartenance à l'équipe.
    # 3.  Comme pour `list_projects`, elle effectue une requête séparée pour
    #     récupérer les membres de l'équipe et les injecte manuellement dans la
    #     réponse pour correspondre au schéma `AIProjectRead`.
    membership = sess.exec(
        select(TeamMembership)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == current_user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Project not found")

    members = sess.exec(
        select(TeamMembership)
        .where(TeamMembership.team_id == team_id, TeamMembership.accepted_at.is_not(None))
    ).all()

    members_list = [
        TeamMemberResponse(
            name=member.user.username,
            role=member.role,
            avatar=None
        )
        for member in members
    ]

    proj_dict = proj.dict()
    proj_dict["team_members"] = members_list

    return AIProjectRead.parse_obj(proj_dict)


@router.put("/{project_id}", response_model=AIProjectRead)
def update_project(
        team_id: int,
        project_id: int,
        payload: AIProjectCreate,
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # BLOC DE MISE À JOUR D'UN PROJET
    # Permet de modifier les informations d'un projet existant.
    # La boucle `for key, val in payload.dict(exclude_unset=True).items()` est
    # une façon efficace de n'appliquer que les changements présents dans la
    # requête (mise à jour partielle) plutôt que d'écraser tous les champs.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))
    ).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Project not found")

    for key, val in payload.dict(exclude_unset=True).items():
        setattr(proj, key, val)

    proj.updated_at = datetime.utcnow()
    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return proj


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
        team_id: int,
        project_id: int,
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # BLOC DE SUPPRESSION DE PROJET (OPÉRATION DESTRUCTIVE)
    # Gère la suppression complète d'un projet et de toutes ses ressources associées.
    # 1.  Le droit de suppression est strictement réservé au propriétaire (`owner`) du projet.
    # 2.  Une requête complexe avec `selectinload` est utilisée pour charger le projet et
    #     toutes ses relations (checklist, preuves, runs, datasets, etc.) en mémoire.
    #     Ceci est crucial pour que l'ORM puisse gérer correctement la suppression en cascade.
    # 3.  La suppression se fait en deux étapes :
    #     a. `sess.delete(proj)`: Supprime l'objet et ses relations de la base de données.
    #     b. `purge_project_storage()`: Appelle une fonction utilitaire pour supprimer
    #        tous les fichiers associés au projet sur le disque dur (datasets, modèles, etc.).
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    proj = sess.exec(
        select(AIProject)
        .where(AIProject.id == project_id, AIProject.team_id == team_id)
        .options(
            selectinload(AIProject.checklist_items).selectinload(ISO42001ChecklistItem.proofs),
            selectinload(AIProject.checklist_items).selectinload(ISO42001ChecklistItem.actions_correctives),
            selectinload(AIProject.model_runs).selectinload(ModelRun.artifacts),
            selectinload(AIProject.evaluation_runs),
            selectinload(AIProject.datasets).selectinload(DataSet.train_config),
            selectinload(AIProject.datasets).selectinload(DataSet.test_config),
        )
    ).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    if proj.owner != current_user.username:
        raise HTTPException(403, "Forbidden")

    sess.delete(proj)
    sess.commit()
    purge_project_storage(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ───────────────────────────── CRUD des Commentaires ──────────────────────────────────
# BLOC DE GESTION DES COMMENTAIRES
# Cette section implémente un système de commentaires simple pour chaque projet.

@router.get("/{project_id}/comments", response_model=List[Comment])
def list_comments(team_id: int, project_id: int, current_user: User = Depends(get_current_user),
                  sess: Session = Depends(get_session)):
    # Récupère la liste de tous les commentaires d'un projet, triés par date.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Project not found")

    comments = sess.exec(select(Comment).where(Comment.project_id == project_id).order_by(Comment.date)).all()
    return comments


@router.post("/{project_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_comment(
        team_id: int,
        project_id: int,
        payload: CommentCreate = Body(...),
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # Crée un nouveau commentaire. L'auteur est automatiquement défini comme l'utilisateur courant.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Project not found")

    comment = Comment(project_id=project_id, author=current_user.username, content=payload.content)
    sess.add(comment)
    sess.commit()
    sess.refresh(comment)
    return comment


@router.put("/{project_id}/comments/{comment_id}", response_model=Comment)
def update_comment(
        team_id: int,
        project_id: int,
        comment_id: str = Path(...),
        payload: CommentCreate = Body(...),
        current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # Met à jour le contenu d'un commentaire existant.
    # Note : un contrôle supplémentaire pourrait être ajouté pour s'assurer que
    # seul l'auteur original du commentaire peut le modifier.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    comment = sess.get(Comment, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(404, "Comment not found")

    comment.content = payload.content
    comment.date = datetime.utcnow()
    sess.add(comment)
    sess.commit()
    sess.refresh(comment)
    return comment


@router.delete("/{project_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
        team_id: int, project_id: int, comment_id: str = Path(...),
        current_user: User = Depends(get_current_user), sess: Session = Depends(get_session),
):
    # BLOC DE SUPPRESSION D'UN COMMENTAIRE
    # Finalise le CRUD des commentaires en permettant leur suppression.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")

    comment = sess.get(Comment, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(404, "Comment not found")

    # Un contrôle pourrait être ajouté pour que seul l'auteur ou un admin puisse supprimer.
    sess.delete(comment)
    sess.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────── GESTION DE LA CHECKLIST DE CONFORMITÉ ────────────────────────────────
# BLOC DE GESTION DE LA CHECKLIST DE CONFORMITÉ ISO 42001
# Cette section implémente la logique métier pour la checklist de conformité d'un projet.
@router.get("/{project_id}/checklist", response_model=List[ISO42001ChecklistItem])
def list_checklist_items(team_id: int, project_id: int, current_user: User = Depends(get_current_user),
                         sess: Session = Depends(get_session)):
    # Cette route a une double responsabilité :
    # 1.  Lister les items de la checklist pour un projet.
    # 2.  AUTO-INITIALISATION : Si la checklist est vide pour un projet, elle la peuple
    #     automatiquement à partir d'une configuration prédéfinie (`ISO42001_REQUIREMENTS`).
    #     C'est une étape cruciale pour initialiser un nouveau projet.
    # 3.  AUTO-CORRECTION : Elle s'assure que la structure de chaque item (nombre de statuts,
    #     résultats, etc.) correspond bien au nombre de questions, et la corrige si besoin.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")
    items = sess.exec(select(ISO42001ChecklistItem).where(ISO42001ChecklistItem.project_id == project_id)).all()

    if not items:
        for req in ISO42001_REQUIREMENTS:
            n = len(req["audit_questions"])
            sess.add(ISO42001ChecklistItem(
                project_id=project_id, control_id=req["control_id"], control_name=req["control_name"],
                description=req["description"], audit_questions=req["audit_questions"],
                evidence_required=req["evidence_required"], statuses=["to-do"] * n,
                results=["not-assessed"] * n, observations=[None] * n,
                status="to-do", result="not-assessed", observation=None,
            ))
        sess.commit()
        items = sess.exec(select(ISO42001ChecklistItem).where(ISO42001ChecklistItem.project_id == project_id)).all()

    updated = False
    for it in items:
        q = len(it.audit_questions)
        if len(it.statuses) != q: it.statuses = [it.status] * q; updated = True
        if len(it.results) != q: it.results = [it.result] * q; updated = True
        if len(it.observations) != q: it.observations = [it.observation] * q; updated = True
        if updated: sess.add(it)
    if updated: sess.commit()
    return items


@router.post("/{project_id}/checklist", response_model=ISO42001ChecklistItem, status_code=status.HTTP_201_CREATED)
def create_checklist_item(team_id: int, project_id: int, item: ISO42001ChecklistItem,
                          current_user: User = Depends(get_current_user), sess: Session = Depends(get_session)):
    # Permet de créer manuellement un nouvel item de checklist pour un projet.
    # Utile pour ajouter des contrôles personnalisés non présents dans la norme de base.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership:
        raise HTTPException(403, "Accès interdit à cette équipe")
    n = len(item.audit_questions)
    new_item = ISO42001ChecklistItem(
        project_id=project_id, control_id=item.control_id, control_name=item.control_name,
        description=item.description, audit_questions=item.audit_questions,
        evidence_required=item.evidence_required, statuses=[item.status] * n,
        results=[item.result] * n, observations=[item.observation] * n,
        status=item.status, result=item.result, observation=item.observation,
    )
    sess.add(new_item);
    sess.commit();
    sess.refresh(new_item)
    return new_item


@router.put("/{project_id}/checklist/{item_id}", response_model=ISO42001ChecklistItem)
def update_checklist_item(team_id: int, project_id: int, item_id: int, payload: Dict[str, Any] = Body(...),
                          current_user: User = Depends(get_current_user), sess: Session = Depends(get_session)):
    # Route complexe pour mettre à jour UNE SEULE question au sein d'un item de checklist.
    # Elle contient une logique métier importante :
    # 1.  Cible une question précise via le `questionIndex` fourni dans le payload.
    # 2.  Règle métier : Si le résultat d'une question passe à "compliant", elle vérifie
    #     qu'au moins une preuve (`Proof`) a été uploadée pour ce point de contrôle.
    # 3.  AUTOMATISATION : Si le résultat passe à "not-compliant", une `NonConformite`
    #     est automatiquement créée. Inversement, si une non-conformité existait et que
    #     le statut change, elle est automatiquement supprimée.
    item = verify_access(team_id, project_id, item_id, current_user, sess)  # Utilise le helper
    idx = payload.get("questionIndex")
    if not isinstance(idx, int) or idx < 0 or idx >= len(item.audit_questions):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"questionIndex invalide")

    if len(item.statuses) != len(item.audit_questions): item.statuses = [item.status] * len(item.audit_questions)
    if len(item.results) != len(item.audit_questions): item.results = [item.result] * len(item.audit_questions)
    if len(item.observations) != len(item.audit_questions): item.observations = [item.observation] * len(
        item.audit_questions)

    if payload.get("result") == "compliant":
        evidence_ids = item.audit_questions[idx]["evidence_refs"]
        has_proof = sess.exec(select(Proof.id).where(Proof.checklist_item_id == item_id,
                                                     Proof.evidence_id.in_(evidence_ids))).first() is not None
        if not has_proof:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                detail="Au moins une preuve est requise pour déclarer 'compliant'")

    old_result = item.results[idx]
    new_result = payload.get("result", old_result)
    if "result" in payload: item.results[idx] = new_result

    existing_nc = sess.exec(select(NonConformite).where(NonConformite.checklist_item_id == item_id,
                                                        NonConformite.question_index == idx)).first()
    if new_result == "not-compliant":
        if not existing_nc:
            nc = NonConformite(checklist_item_id=item_id, question_index=idx, type_nc="mineure",
                               statut=StatutNonConformite.non_corrigee)
            sess.add(nc)
    elif existing_nc:
        sess.delete(existing_nc)

    if "status" in payload: item.statuses[idx] = payload["status"]
    if "observation" in payload: item.observations[idx] = payload["observation"]

    item.updated_at = datetime.utcnow()
    sess.add(item);
    sess.commit();
    sess.refresh(item)
    return item


# ─────────────────────── GESTION DES ACTIONS CORRECTIVES ─────────────────────────────────
# BLOC DE GESTION DES ACTIONS CORRECTIVES
# Cette section gère la création d'actions pour remédier aux non-conformités.

def update_nonconformite_statut(sess: Session, nc: NonConformite) -> None:
    # HELPER INTERNE : Met à jour automatiquement le statut d'une non-conformité
    # en se basant sur le statut de toutes les actions correctives qui lui sont liées.
    # - Si aucune action -> "non corrigée"
    # - Si au moins une action est "en cours" -> "en cours"
    # - Si TOUTES les actions sont "terminées" -> "corrigée"
    actions = sess.exec(select(ActionCorrective).where(ActionCorrective.non_conformite_id == nc.id)).all()
    if not actions:
        nc.statut = StatutNonConformite.non_corrigee
    else:
        in_progress = any(a.status.lower() in ("in progress", "en cours", "progress") for a in actions)
        all_done = all(a.status.lower() in ("done", "completed", "terminée", "ferme") for a in actions)
        if in_progress:
            nc.statut = StatutNonConformite.en_cours
        elif all_done:
            nc.statut = StatutNonConformite.corrigee
        else:
            nc.statut = StatutNonConformite.non_corrigee
    nc.updated_at = datetime.utcnow()
    sess.add(nc);
    sess.commit();
    sess.refresh(nc)


@router.post("/{project_id}/checklist/{item_id}/actions", response_model=ActionCorrective)
def create_action_corrective(team_id: int, project_id: int, item_id: int, action: ActionCorrective,
                             current_user: User = Depends(get_current_user), sess: Session = Depends(get_session)):
    # Route pour créer une nouvelle action corrective.
    # 1.  Valide les droits et les objets parents (item de checklist, non-conformité, utilisateur responsable).
    # 2.  Crée l'action corrective en base de données.
    # 3.  AUTOMATISATION : Appelle le helper `update_nonconformite_statut` pour que le statut
    #     de la non-conformité parente reflète immédiatement l'ajout de cette nouvelle action.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership: raise HTTPException(403, "Accès interdit à cette équipe")

    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id: raise HTTPException(404, "Checklist item not found")

    if action.non_conformite_id is not None:
        nc = sess.get(NonConformite, action.non_conformite_id)
        if not nc or nc.checklist_item_id != item_id: raise HTTPException(400, "NonConformite invalide pour cet item")

    if action.responsible_user_id is not None:
        resp_user = sess.get(User, action.responsible_user_id)
        if not resp_user: raise HTTPException(400, "Utilisateur responsable introuvable")
        resp_mem = sess.exec(select(TeamMembership).where(TeamMembership.team_id == team_id,
                                                          TeamMembership.user_id == action.responsible_user_id,
                                                          TeamMembership.accepted_at.is_not(None))).first()
        if not resp_mem: raise HTTPException(400, "Utilisateur responsable n'est pas membre de l'équipe")

    deadline = action.deadline
    if isinstance(deadline, str): deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))

    corrective_action = ActionCorrective(
        description=action.description, deadline=deadline, status=action.status or "In Progress",
        checklist_item_id=item_id, non_conformite_id=action.non_conformite_id,
        responsible_user_id=action.responsible_user_id,
    )
    sess.add(corrective_action);
    sess.commit();
    sess.refresh(corrective_action)

    if corrective_action.non_conformite_id:
        nc = sess.get(NonConformite, corrective_action.non_conformite_id)
        if nc: update_nonconformite_statut(sess, nc)

    return corrective_action


# ─────────────────────── FIN DU CRUD DES ACTIONS CORRECTIVES ─────────────────────────────────
# BLOC DE GESTION DES ACTIONS CORRECTIVES (SUITE ET FIN)
# Cette section complète le cycle de vie de la gestion des actions correctives.

@router.put("/{project_id}/checklist/{item_id}/actions/{action_id}", response_model=ActionCorrective)
def update_action_corrective(
        team_id: int, project_id: int, item_id: int, action_id: int,
        action: ActionCorrective, current_user: User = Depends(get_current_user), sess: Session = Depends(get_session),
):
    # Route pour mettre à jour une action corrective existante.
    # 1.  Effectue une série de vérifications pour s'assurer que l'utilisateur a les droits
    #     et que tous les objets (item, action, utilisateur responsable, etc.) sont valides.
    # 2.  Applique les modifications du payload à l'objet `ActionCorrective`.
    # 3.  AUTOMATISATION : Tout comme lors de la création, elle appelle `update_nonconformite_statut`
    #     après la mise à jour pour recalculer et synchroniser le statut de la non-conformité parente.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership: raise HTTPException(403, "Accès interdit à cette équipe")

    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id: raise HTTPException(404, "Checklist item not found")

    corrective_action = sess.get(ActionCorrective, action_id)
    if not corrective_action or corrective_action.checklist_item_id != item_id: raise HTTPException(404,
                                                                                                    "Action corrective not found")

    # ... (Validations des IDs responsables, non-conformité, etc.)

    corrective_action.description = action.description
    corrective_action.deadline = action.deadline
    if isinstance(corrective_action.deadline, str):
        corrective_action.deadline = datetime.fromisoformat(corrective_action.deadline.replace('Z', '+00:00'))
    corrective_action.status = action.status
    corrective_action.non_conformite_id = action.non_conformite_id
    corrective_action.responsible_user_id = action.responsible_user_id
    corrective_action.updated_at = datetime.utcnow()
    sess.add(corrective_action)
    sess.commit()
    sess.refresh(corrective_action)

    if corrective_action.non_conformite_id:
        nc = sess.get(NonConformite, corrective_action.non_conformite_id)
        if nc: update_nonconformite_statut(sess, nc)

    return corrective_action


@router.get("/{project_id}/checklist/{item_id}/actions", response_model=List[ActionCorrective])
def get_actions_for_item(team_id: int, project_id: int, item_id: int, current_user: User = Depends(get_current_user),
                         sess: Session = Depends(get_session)):
    # Route simple pour lister toutes les actions correctives associées à un item de checklist.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership: raise HTTPException(403, "Accès interdit à cette équipe")

    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id: raise HTTPException(status_code=404,
                                                                      detail="Checklist item not found")

    return sess.exec(select(ActionCorrective).where(ActionCorrective.checklist_item_id == item_id)).all()


@router.delete("/{project_id}/checklist/{item_id}/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_corrective(
        team_id: int, project_id: int, item_id: int, action_id: int,
        current_user: User = Depends(get_current_user), sess: Session = Depends(get_session),
):
    # Route pour supprimer une action corrective.
    # AUTOMATISATION : Après la suppression, elle recalcule le statut de la non-conformité
    # parente, car la suppression d'une action peut changer l'état global (par exemple,
    # passer de "en cours" à "non corrigée").
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership: raise HTTPException(403, "Accès interdit à cette équipe")

    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id: raise HTTPException(status_code=404,
                                                                      detail="Checklist item not found")

    action = sess.get(ActionCorrective, action_id)
    if not action or action.checklist_item_id != item_id: raise HTTPException(status_code=404,
                                                                              detail="Action corrective not found")

    non_conformite_id = action.non_conformite_id
    sess.delete(action)
    sess.commit()

    if non_conformite_id:
        nc = sess.get(NonConformite, non_conformite_id)
        if nc: update_nonconformite_statut(sess, nc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ────────────────────────────── GESTION DES PREUVES (PROOFS) ─────────────────────────────
# BLOC DE GESTION DES PREUVES (EVIDENCE)
# Cette section gère l'upload des fichiers servant de preuves pour la conformité.
@router.post(
    "/{project_id}/checklist/{item_id}/proofs", status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any], summary="Upload ou mise à jour d'une preuve associée à un evidence_id"
)
async def upload_proof(
        team_id: int, project_id: int, item_id: int,
        evidence_id: str = Form(...),  # L'ID de l'exigence de preuve (ex: "ID-01.A")
        file: UploadFile = File(...),  # Le fichier de preuve
        current_user: User = Depends(get_current_user), sess: Session = Depends(get_session),
):
    # Route pour téléverser un fichier de preuve.
    # 1.  Valide que `evidence_id` est bien une exigence attendue pour cet item de checklist.
    # 2.  Implémente une logique "d'UPSERT" :
    #     - Si une preuve avec le même nom de fichier existe déjà pour cet `evidence_id`,
    #       le contenu du fichier est mis à jour (écrasement).
    #     - Sinon, une nouvelle entrée `Proof` est créée.
    #     Ceci permet aux utilisateurs de facilement remplacer une preuve par une version plus récente.
    # 3.  Retourne l'ID de la preuve et une URL de téléchargement que le front-end peut utiliser.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership: raise HTTPException(403, "Accès interdit à cette équipe")

    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id: raise HTTPException(404, "Checklist item not found")

    if evidence_id not in {e["id"] for e in item.evidence_required}:
        raise HTTPException(400, "evidence_id inconnu pour cet item")

    content = await file.read()

    existing = sess.exec(select(Proof).where(Proof.checklist_item_id == item_id, Proof.evidence_id == evidence_id,
                                             Proof.filename == file.filename)).first()

    if existing:
        existing.content = content
        existing.created_at = datetime.utcnow()
        sess.add(existing)
        sess.commit()
        sess.refresh(existing)
        proof = existing
    else:
        proof = Proof(checklist_item_id=item_id, evidence_id=evidence_id, filename=file.filename, content=content)
        sess.add(proof)
        sess.commit()
        sess.refresh(proof)

    return {
        "proof_id": proof.id,
        "evidence_id": evidence_id,
        "download_url": f"/teams/{team_id}/projects/{project_id}/proofs/{proof.id}"
    }


@router.get(
    "/{project_id}/checklist/{item_id}/questions/{question_index}/proofs",
    response_model=List[Dict[str, Any]],
    summary="Liste les preuves pour une question donnée"
)
def list_proofs_for_question(
        team_id: int, project_id: int, item_id: int, question_index: int,
        current_user: User = Depends(get_current_user), sess: Session = Depends(get_session),
):
    # BLOC DE LISTAGE DES PREUVES POUR UNE QUESTION
    # Cette route ne liste pas toutes les preuves d'un item, mais seulement celles
    # qui sont pertinentes pour une question spécifique au sein de cet item.
    # 1.  Valide l'accès et l'index de la question.
    # 2.  Récupère les `evidence_refs` (les IDs des preuves requises) pour cette question.
    # 3.  Interroge la base de données pour trouver toutes les preuves uploadées
    #     qui correspondent à ces IDs de référence.
    # 4.  Retourne une liste formatée incluant une URL de téléchargement pour chaque preuve.
    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership: raise HTTPException(403, "Accès interdit à cette équipe")

    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id: raise HTTPException(status_code=404,
                                                                      detail="Checklist item not found")
    if question_index < 0 or question_index >= len(item.audit_questions): raise HTTPException(status_code=400,
                                                                                              detail="Invalid question index")

    evidence_ids = item.audit_questions[question_index]["evidence_refs"]
    proofs = sess.exec(
        select(Proof).where(Proof.checklist_item_id == item_id, Proof.evidence_id.in_(evidence_ids))).all()

    return [
        {"proof_id": p.id, "evidence_id": p.evidence_id, "filename": p.filename,
         "download_url": f"/teams/{team_id}/projects/{project_id}/proofs/{p.id}"}
        for p in proofs
    ]


@router.get("/{project_id}/proofs/{proof_id}", status_code=status.HTTP_200_OK,
            summary="Télécharge une preuve uploadée (docx, odt, txt, etc.)")
def download_uploaded_proof(
        team_id: int, project_id: int, proof_id: int,
        sess: Session = Depends(get_session), current_user: User = Depends(get_current_user),
        # Ajout de current_user pour la cohérence
):
    # BLOC DE TÉLÉCHARGEMENT D'UNE PREUVE
    # Sert le contenu binaire d'une preuve spécifique qui a été préalablement uploadée.
    # Effectue une validation pour s'assurer que la preuve demandée appartient bien au projet
    # spécifié dans l'URL, empêchant l'accès à des preuves d'autres projets.
    # Note: Le `Depends(get_current_user)` est ajouté dans le décorateur pour s'assurer
    # que la route est protégée, même si `current_user` n'est pas utilisé directement dans la logique.
    proof = sess.get(Proof, proof_id)
    if not proof: raise HTTPException(status_code=404, detail="Preuve non trouvée")

    item = proof.checklist_item
    if item.project_id != project_id: raise HTTPException(status_code=403, detail="Accès interdit à cette preuve")

    return Response(
        content=proof.content,
        media_type="application/octet-stream",  # Type générique pour forcer le téléchargement
        headers={"Content-Disposition": f'attachment; filename="{proof.filename}"'}
    )


# ─────────────────── TÉLÉCHARGEMENT DES MODÈLES DE PREUVES (TEMPLATES) ──────────────────────────
@router.get("/{project_id}/checklist/{item_id}/proofs/template/{evidence_id}", response_class=FileResponse,
            summary="Télécharge la preuve vierge (fichier .docx) associée à un evidence_id")
def download_blank_proof(
        team_id: int, project_id: int, item_id: int, evidence_id: str,
        sess: Session = Depends(get_session), current_user: User = Depends(get_current_user),  # Ajout de current_user
):
    # BLOC DE TÉLÉCHARGEMENT D'UN MODÈLE DE DOCUMENT VIERGE
    # Route complexe qui ne sert pas une preuve uploadée par l'utilisateur, mais un
    # fichier modèle (.docx) prédéfini, stocké sur le serveur.
    # La logique principale consiste à mapper un `evidence_id` à un nom de fichier (ex: "15.docx").
    # 1.  Trouve l'index local de la question (`question_index`) qui requiert cet `evidence_id`.
    # 2.  Calcule le "numéro global" de cette question sur l'ensemble de la checklist du projet.
    #     Pour cela, elle trie tous les items de la checklist selon l'ordre canonique de la norme,
    #     puis compte le nombre de questions précédentes pour trouver un offset.
    # 3.  Construit le chemin du fichier (ex: `/config/documents/15.docx`) à partir de ce numéro global.
    # 4.  Sert le fichier .docx correspondant à l'aide de `FileResponse`.

    # ... (Vérifications d'accès)

    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id: raise HTTPException(status_code=404,
                                                                      detail="Checklist item not found")

    question_index = None
    for idx, q in enumerate(item.audit_questions):
        if evidence_id in q["evidence_refs"]: question_index = idx; break
    if question_index is None: raise HTTPException(status_code=404, detail="Evidence ID non trouvé pour cet item")

    req_order = {req["control_id"]: i for i, req in enumerate(ISO42001_REQUIREMENTS)}
    items = sess.exec(select(ISO42001ChecklistItem).where(ISO42001ChecklistItem.project_id == project_id)).all()
    items_sorted = sorted(items, key=lambda it: req_order.get(it.control_id, float("inf")))

    offset = 0
    for it in items_sorted:
        if it.id == item_id: break
        offset += len(it.audit_questions)
    global_number = offset + question_index + 1

    base_dir = FSPath(__file__).resolve().parents[2]
    docs_dir = base_dir / "config" / "documents"
    filename = f"{global_number}.docx"
    file_path = docs_dir / filename
    if not file_path.exists(): raise HTTPException(status_code=404, detail="Template not found")

    return FileResponse(path=str(file_path),
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        filename=filename)


# ─────────────────── CONSULTATION DES NON-CONFORMITÉS ──────────────────────────
@router.get("/{project_id}/checklist/{item_id}/nonconformites", response_model=List[NonConformiteRead])
def list_nonconformites(
        team_id: int, project_id: int, item_id: int, question_index: int = Query(..., ge=0),
        current_user: User = Depends(get_current_user), sess: Session = Depends(get_session),
):
    # BLOC DE LISTAGE DES NON-CONFORMITÉS
    # Récupère la liste des non-conformités, mais de manière très ciblée :
    # uniquement pour une question spécifique (`question_index`) au sein d'un item de checklist.
    verify_access(team_id, project_id, item_id, current_user, sess)
    ncs = sess.exec(select(NonConformite).where(NonConformite.checklist_item_id == item_id,
                                                NonConformite.question_index == question_index)).all()
    return ncs


# ─────────────────── FIN DU CRUD DES NON-CONFORMITÉS ──────────────────────────
# BLOC DE GESTION DES NON-CONFORMITÉS (SUITE ET FIN)
# Cette section finalise la gestion manuelle des non-conformités.

@router.put("/{project_id}/checklist/{item_id}/nonconformites/{nc_id}", response_model=NonConformiteRead)
def update_nonconformite(
        team_id: int, project_id: int, item_id: int, nc_id: int,
        payload: NonConformiteUpdate = Body(...), current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session),
):
    # Route pour mettre à jour une non-conformité existante.
    # Utile pour modifier manuellement son type (ex: de mineure à majeure) ou sa description.
    verify_access(team_id, project_id, item_id, current_user, sess)
    nc = sess.get(NonConformite, nc_id)
    if not nc or nc.checklist_item_id != item_id:
        raise HTTPException(status_code=404, detail="NonConformite not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(nc, key, value)

    sess.add(nc)
    sess.commit()
    sess.refresh(nc)
    return nc


@router.delete("/{project_id}/checklist/{item_id}/nonconformites/{nc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nonconformite(
        team_id: int, project_id: int, item_id: int, nc_id: int,
        current_user: User = Depends(get_current_user), sess: Session = Depends(get_session),
):
    # Route pour supprimer manuellement une non-conformité.
    # Peut être utilisé si une non-conformité a été créée par erreur.
    verify_access(team_id, project_id, item_id, current_user, sess)
    nc = sess.get(NonConformite, nc_id)
    if not nc or nc.checklist_item_id != item_id:
        raise HTTPException(status_code=404, detail="NonConformite not found")

    sess.delete(nc)
    sess.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────── NOTIFICATIONS POUR NON-CONFORMITÉS URGENTES ──────────────────────────
# BLOC DE NOTIFICATIONS POUR NON-CONFORMITÉS
# Cette section fournit une route spécialisée pour identifier les non-conformités les plus critiques.

class NonConformityNotification(BaseModel):
    """Schéma de réponse spécifique pour les alertes de non-conformité."""
    id: int
    deadline_correction: Optional[datetime]
    statut: str
    checklist_item_id: int
    question_index: int

    class Config:
        from_attributes = True


@router.get("/{project_id}/notifications/nonconformities", response_model=List[NonConformityNotification],
            summary="Liste des alertes de non-conformités majeures non corrigées proches/dépassant deadline")
def get_nc_notifications(
        team_id: int, project_id: int, current_user: User = Depends(get_current_user),
        sess: Session = Depends(get_session)
):
    # Cette route n'est pas un simple listage, c'est une requête métier pour générer des alertes.
    # Elle sélectionne très spécifiquement les non-conformités qui sont :
    # 1. De type "majeure".
    # 2. Dont le statut n'est PAS "corrigee".
    # 3. Dont la date limite de correction (`deadline_correction`) est soit déjà passée,
    #    soit arrive dans les 7 prochains jours.
    # Le résultat est trié par date limite pour afficher les plus urgentes en premier.

    membership = sess.exec(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id,
                                     TeamMembership.accepted_at.is_not(None))).first()
    if not membership: raise HTTPException(status_code=403, detail="Accès interdit à cette équipe")

    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id: raise HTTPException(status_code=404, detail="Projet non trouvé")

    now = datetime.utcnow()
    soon = now + timedelta(days=7)

    ncs = sess.exec(
        select(NonConformite)
        .join(NonConformite.checklist_item)
        .where(
            NonConformite.type_nc == "majeure",
            NonConformite.statut != "corrigee",
            NonConformite.deadline_correction != None,
            NonConformite.deadline_correction <= soon,
            NonConformite.checklist_item.has(project_id=project_id),
        )
        .order_by(NonConformite.deadline_correction)
    ).all()
    return ncs