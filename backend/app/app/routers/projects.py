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
from sqlalchemy.orm import selectinload   # pour charger les enfants en une requête
router = APIRouter(prefix="/teams/{team_id}/projects", tags=["projects"])


# --------Helper---------

# Authorization helper (reuse in all routes)
def verify_access(
    team_id: int,
    project_id: int,
    item_id: int,
    current_user: User,
    sess: Session,
) -> ISO42001ChecklistItem:
    # Verify team membership
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

    # Verify project belongs to team
    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify checklist item belongs to project
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    return item



# ─────────────────────────── PROJECT CRUD ────────────────────────────────────
@router.post("/", response_model=AIProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    team_id: int,
    payload: AIProjectCreate,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # 1) vérifier que l'utilisateur est bien membre de l'équipe
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
      # 2) forcer le team_id dans le payload
    proj = AIProject(**payload.dict(), team_id=team_id)
    proj.owner = current_user.username
    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return proj

from app.models import TeamMemberResponse  # Assure-toi d'importer ce schéma Pydantic

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
    # Vérifier que l'utilisateur est membre de l'équipe
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

    # Construire la requête des projets
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

    # Charger la team et ses membres pour éviter N+1 queries
    query = query.options(
        selectinload(AIProject.team)
        .selectinload(Team.members)
        .selectinload(TeamMembership.user)
    )

    projects = sess.exec(query.offset(skip).limit(limit)).all()

    # Construire la liste des projets avec team_members injectés
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
                            avatar=None  # ou mem.user.avatar si tu as ce champ
                        )
                    )
        # Transformer l'objet projet en dict et injecter la liste des membres
        proj_dict = proj.dict()
        proj_dict["team_members"] = members_list
        results.append(proj_dict)

    # Retourner la liste des projets convertie en modèles Pydantic
    return [AIProjectRead.parse_obj(p) for p in results]




from sqlalchemy.orm import selectinload

@router.get("/{project_id}", response_model=AIProjectRead)
def read_project(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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

    # Charger les membres de l'équipe associés
    members = sess.exec(
        select(TeamMembership)
        .where(TeamMembership.team_id == team_id, TeamMembership.accepted_at.is_not(None))
    ).all()

    # Construire la liste à retourner
    members_list = [
        TeamMemberResponse(
            name=member.user.username,
            role=member.role,
            avatar=None  # ou member.user.avatar si tu as ce champ
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
    proj = sess.exec(
        select(AIProject)
        .where(AIProject.id == project_id, AIProject.team_id == team_id)
        .options(
            selectinload(AIProject.checklist_items)
            .selectinload(ISO42001ChecklistItem.proofs),
            selectinload(AIProject.checklist_items)
            .selectinload(ISO42001ChecklistItem.actions_correctives),
            selectinload(AIProject.model_runs)
            .selectinload(ModelRun.artifacts),
            selectinload(AIProject.evaluation_runs),
            # 🎯 here are the two separate dataset‐config loaders:
            selectinload(AIProject.datasets)
            .selectinload(DataSet.train_config),
            selectinload(AIProject.datasets)
            .selectinload(DataSet.test_config),
        )
    ).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    if proj.owner != current_user.username:
        raise HTTPException(403, "Forbidden")

    # 1. suppression en base (cascade géré par ORM)
    sess.delete(proj)
    sess.commit()

    # 2. suppression sur disque
    purge_project_storage(project_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ───────────────────────────── COMMENTS ──────────────────────────────────────
@router.get("/{project_id}/comments", response_model=List[Comment])
def list_comments(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # Vérifier que l'utilisateur appartient bien à l'équipe (comme avant)
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

    # Vérifier que le projet appartient bien à l'équipe
    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Project not found")

    comments = sess.exec(
        select(Comment).where(Comment.project_id == project_id).order_by(Comment.date)
    ).all()
    return comments

@router.post("/{project_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_comment(
    team_id: int,
    project_id: int,
    payload: CommentCreate = Body(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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

    comment = Comment(
        project_id=project_id,
        author=current_user.username,
        content=payload.content,
    )
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

    comment = sess.get(Comment, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(404, "Comment not found")

    # Optionnel: vérifier que l'auteur est current_user.username (contrôle accès)

    comment.content = payload.content
    comment.date = datetime.utcnow()
    sess.add(comment)
    sess.commit()
    sess.refresh(comment)
    return comment


@router.delete("/{project_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    team_id: int,
    project_id: int,
    comment_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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

    comment = sess.get(Comment, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(404, "Comment not found")

    sess.delete(comment)
    sess.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)



# ─────────────────────────── CHECKLIST ITEMS ────────────────────────────────
@router.get(
    "/{project_id}/checklist",
    response_model=List[ISO42001ChecklistItem],
    summary="Liste complète des items (avec leurs tableaux `statuses` et `results`)"
)
def list_checklist_items(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    items = sess.exec(
        select(ISO42001ChecklistItem)
        .where(ISO42001ChecklistItem.project_id == project_id)
    ).all()

    # Seed initial items si nécessaire
    if not items:
        for req in ISO42001_REQUIREMENTS:
            n = len(req["audit_questions"])
            sess.add(
                ISO42001ChecklistItem(
                    project_id=project_id,
                    control_id=req["control_id"],
                    control_name=req["control_name"],
                    description=req["description"],
                    audit_questions=req["audit_questions"],
                    evidence_required=req["evidence_required"],
                    statuses=["to-do"] * n,
                    results=["not-assessed"] * n,
                    observations=[None] * n,
                    status="to-do",
                    result="not-assessed",
                    observation=None,
                )
            )
        sess.commit()
        items = sess.exec(
            select(ISO42001ChecklistItem)
            .where(ISO42001ChecklistItem.project_id == project_id)
        ).all()

    # Ré-aligne la longueur des tableaux si le config a changé
    updated = False
    for it in items:
        q = len(it.audit_questions)
        if len(it.statuses) != q:
            it.statuses = [it.status] * q
            updated = True
        if len(it.results) != q:
            it.results = [it.result] * q
            updated = True
        if len(it.observations) != q:
            it.observations = [it.observation] * q
            updated = True
        if updated:
            sess.add(it)
    if updated:
        sess.commit()

    return items


@router.post("/{project_id}/checklist", response_model=ISO42001ChecklistItem, status_code=status.HTTP_201_CREATED)
def create_checklist_item(
    team_id:int,
    project_id: int,
    item: ISO42001ChecklistItem,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    n = len(item.audit_questions)
    new_item = ISO42001ChecklistItem(
        project_id=project_id,
        control_id=item.control_id,
        control_name=item.control_name,
        description=item.description,
        audit_questions=item.audit_questions,
        evidence_required=item.evidence_required,
        statuses=[item.status] * n,
        results=[item.result] * n,
        observations=[item.observation] * n,
        status=item.status,
        result=item.result,
        observation=item.observation,
    )
    sess.add(new_item)
    sess.commit()
    sess.refresh(new_item)
    return new_item


@router.put(
    "/{project_id}/checklist/{item_id}",
    response_model=ISO42001ChecklistItem,
    status_code=status.HTTP_200_OK
)
def update_checklist_item(
    team_id: int,
    project_id: int,
    item_id: int,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    idx = payload.get("questionIndex")
    if not isinstance(idx, int) or idx < 0 or idx >= len(item.audit_questions):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"questionIndex invalide, doit être entre 0 et {len(item.audit_questions)-1}"
        )

    # Assure la bonne longueur des tableaux
    q = len(item.audit_questions)
    if len(item.statuses) != q:
        item.statuses = [item.status] * q
    if len(item.results) != q:
        item.results = [item.result] * q
    if len(item.observations) != q:
        item.observations = [item.observation] * q

    # Si on passe à 'compliant', on exige au moins une preuve pour l'un des evidence_id
    if payload.get("result") == "compliant":
        evidence_ids = item.audit_questions[idx]["evidence_refs"]
        has_proof = sess.exec(
            select(Proof.id)
            .where(
                Proof.checklist_item_id == item_id,
                Proof.evidence_id.in_(evidence_ids)
            )
        ).first() is not None
        if not has_proof:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Au moins une preuve est requise pour déclarer 'compliant'"
            )

    # Applique les changements
    if "status" in payload:
        item.statuses[idx] = payload["status"]
    # Récupérer l'ancien résultat
    old_result = item.results[idx]
    new_result = payload.get("result", old_result)

    # Mise à jour du résultat dans item.results
    if "result" in payload:
        item.results[idx] = new_result

    question_index = idx

    # Cherche une NonConformité existante pour cet item et cette question
    existing_nc = sess.exec(
        select(NonConformite)
        .where(
            NonConformite.checklist_item_id == item_id,
            NonConformite.question_index == question_index
        )
    ).first()

    if new_result == "not-compliant":
        if not existing_nc:
            # Création automatique d'une NonConformité
            nc = NonConformite(
            checklist_item_id = item_id,
            question_index = question_index,
            type_nc = "mineure",
            statut = StatutNonConformite.non_corrigee,
            )
            sess.add(nc)
    elif existing_nc:
        # Suppression de la NonConformité existante si le résultat change
        sess.delete(existing_nc)
    if "observation" in payload:
        item.observations[idx] = payload["observation"]

    item.updated_at = datetime.utcnow()
    sess.add(item)
    sess.commit()
    sess.refresh(item)
    return item


# ─────────────────────── CORRECTIVE ACTIONS ─────────────────────────────────
def update_nonconformite_statut(sess: Session, nc: NonConformite) -> None:
    actions = sess.exec(
        select(ActionCorrective).where(ActionCorrective.non_conformite_id == nc.id)
    ).all()

    if not actions:
        nc.statut = StatutNonConformite.non_corrigee
    else:
        # si au moins une action status "In Progress" ou autre état actif
        in_progress = any(a.status.lower() in ("in progress", "en cours", "progress") for a in actions)
        all_done = all(a.status.lower() in ("done", "completed", "terminée", "ferme") for a in actions)

        if in_progress:
            nc.statut = StatutNonConformite.en_cours
        elif all_done:
            nc.statut = StatutNonConformite.corrigee
        else:
            # Par défaut si ni tout terminé ni en cours, considérer non corrigée
            nc.statut = StatutNonConformite.non_corrigee

    nc.updated_at = datetime.utcnow()
    sess.add(nc)
    sess.commit()
    sess.refresh(nc)


@router.post("/{project_id}/checklist/{item_id}/actions", response_model=ActionCorrective)
def create_action_corrective(
    team_id: int,
    project_id: int,
    item_id: int,
    action: ActionCorrective,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # Vérification appartenance équipe
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

    # Vérifier checklist item
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(404, "Checklist item not found")

    # Si non_conformite_id est fourni, vérifier qu'elle existe et appartient à cet item
    if action.non_conformite_id is not None:
        nc = sess.get(NonConformite, action.non_conformite_id)
        if not nc or nc.checklist_item_id != item_id:
            raise HTTPException(400, "NonConformite invalide pour cet item")

    # Si responsible_user_id est fourni, vérifier que l'utilisateur existe et est membre de l'équipe
    if action.responsible_user_id is not None:
        resp_user = sess.get(User, action.responsible_user_id)
        if not resp_user:
            raise HTTPException(400, "Utilisateur responsable introuvable")
        resp_mem = sess.exec(
            select(TeamMembership)
            .where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == action.responsible_user_id,
                TeamMembership.accepted_at.is_not(None),
            )
        ).first()
        if not resp_mem:
            raise HTTPException(400, "Utilisateur responsable n'est pas membre de l'équipe")
    deadline = action.deadline
    if isinstance(deadline, str):
        # Convertir la chaîne ISO 8601 en datetime en remplaçant 'Z' par '+00:00' si besoin
        deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))

    corrective_action = ActionCorrective(
        description=action.description,
        deadline=deadline,
        status=action.status or "In Progress",
        checklist_item_id=item_id,
        non_conformite_id=action.non_conformite_id,
        responsible_user_id=action.responsible_user_id,
    )
    sess.add(corrective_action)
    sess.commit()
    sess.refresh(corrective_action)
    # Mise à jour automatique du statut de la non-conformité liée
    if corrective_action.non_conformite_id:
        nc = sess.get(NonConformite, corrective_action.non_conformite_id)
        if nc:
            update_nonconformite_statut(sess, nc)

    return corrective_action


@router.put("/{project_id}/checklist/{item_id}/actions/{action_id}", response_model=ActionCorrective)
def update_action_corrective(
    team_id: int,
    project_id: int,
    item_id: int,
    action_id: int,
    action: ActionCorrective,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # Vérification appartenance équipe
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

    # Vérifier checklist item
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(404, "Checklist item not found")

    corrective_action = sess.get(ActionCorrective, action_id)
    if not corrective_action or corrective_action.checklist_item_id != item_id:
        raise HTTPException(404, "Action corrective not found")

    # Si non_conformite_id est fourni, vérifier qu'elle existe et appartient à cet item
    if action.non_conformite_id is not None:
        nc = sess.get(NonConformite, action.non_conformite_id)
        if not nc or nc.checklist_item_id != item_id:
            raise HTTPException(400, "NonConformite invalide pour cet item")

    # Si responsible_user_id est fourni, vérifier que l'utilisateur existe et est membre de l'équipe
    if action.responsible_user_id is not None:
        resp_user = sess.get(User, action.responsible_user_id)
        if not resp_user:
            raise HTTPException(400, "Utilisateur responsable introuvable")
        resp_mem = sess.exec(
            select(TeamMembership)
            .where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == action.responsible_user_id,
                TeamMembership.accepted_at.is_not(None),
            )
        ).first()
        if not resp_mem:
            raise HTTPException(400, "Utilisateur responsable n'est pas membre de l'équipe")

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
        if nc:
            update_nonconformite_statut(sess, nc)

    return corrective_action


@router.get("/{project_id}/checklist/{item_id}/actions", response_model=List[ActionCorrective])
def get_actions_for_item(
    team_id: int,
    project_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return sess.exec(
        select(ActionCorrective).where(ActionCorrective.checklist_item_id == item_id)
    ).all()


@router.delete("/{project_id}/checklist/{item_id}/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_corrective(
    team_id: int,
    project_id: int,
    item_id: int,
    action_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    action = sess.get(ActionCorrective, action_id)
    if not action or action.checklist_item_id != item_id:
        raise HTTPException(status_code=404, detail="Action corrective not found")
    non_conformite_id = action.non_conformite_id
    sess.delete(action)
    sess.commit()

    if non_conformite_id:
        nc = sess.get(NonConformite, non_conformite_id)
        if nc:
            update_nonconformite_statut(sess, nc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ────────────────────────────── PROOFS (evidence) ─────────────────────────────
@router.post(
    "/{project_id}/checklist/{item_id}/proofs",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
    summary="Upload ou mise à jour d'une preuve associée à un evidence_id"
)
async def upload_proof(
    team_id: int,
    project_id: int,
    item_id: int,
    evidence_id: str = Form(...),   # identifiant de la preuve
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(404, "Checklist item not found")

    # vérifie que l'evidence_id est attendu
    if evidence_id not in {e["id"] for e in item.evidence_required}:
        raise HTTPException(400, "evidence_id inconnu pour cet item")

    content = await file.read()

    # Essaye de trouver une preuve existante
    existing = sess.exec(
        select(Proof)
        .where(
            Proof.checklist_item_id == item_id,
            Proof.evidence_id == evidence_id,
            Proof.filename == file.filename
        )
    ).first()

    if existing:
        # Mise à jour du contenu et du timestamp
        existing.content = content
        existing.created_at = datetime.utcnow()
        sess.add(existing)
        sess.commit()
        sess.refresh(existing)
        proof = existing
    else:
        # Création d'une nouvelle entrée
        proof = Proof(
            checklist_item_id=item_id,
            evidence_id=evidence_id,
            filename=file.filename,
            content=content
        )
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
    team_id: int,
    project_id: int,
    item_id: int,
    question_index: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    if question_index < 0 or question_index >= len(item.audit_questions):
        raise HTTPException(status_code=400, detail="Invalid question index")

    evidence_ids = item.audit_questions[question_index]["evidence_refs"]

    proofs = sess.exec(
        select(Proof).where(
            Proof.checklist_item_id == item_id,
            Proof.evidence_id.in_(evidence_ids)
        )
    ).all()

    return [
        {
            "proof_id": p.id,
            "evidence_id": p.evidence_id,
            "filename": p.filename,
            "download_url": f"/teams/{team_id}/projects/{project_id}/proofs/{p.id}"
        }
        for p in proofs
    ]



@router.get(
    "/{project_id}/proofs/{proof_id}",
    status_code=status.HTTP_200_OK,
    summary="Télécharge une preuve uploadée (docx, odt, txt, etc.)",
    dependencies=[Depends(get_current_user)]
)
def download_uploaded_proof(
    team_id: int,
    project_id: int,
    proof_id: int,
    sess: Session = Depends(get_session),
):
    proof = sess.get(Proof, proof_id)
    if not proof:
        raise HTTPException(status_code=404, detail="Preuve non trouvée")
    # Vérifie que la preuve appartient bien au projet courant
    item = proof.checklist_item
    if item.project_id != project_id:
        raise HTTPException(status_code=403, detail="Accès interdit à cette preuve")

    return Response(
        content=proof.content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{proof.filename}"'
        }
    )
# ────────────────────────────── TEMPLATES ────────────────────────────────────

@router.get(
    "/{project_id}/checklist/{item_id}/proofs/template/{evidence_id}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    summary="Télécharge la preuve vierge (fichier .docx) associée à un evidence_id"
)
def download_blank_proof(
    team_id:int,
    project_id: int,
    item_id: int,
    evidence_id: str,
    sess: Session = Depends(get_session),
):

    # Vérifie projet + item
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    # Trouve l'index de la question qui contient cet evidence_id
    question_index = None
    for idx, q in enumerate(item.audit_questions):
        if evidence_id in q["evidence_refs"]:
            question_index = idx
            break
    if question_index is None:
        raise HTTPException(status_code=404, detail="Evidence ID non trouvé pour cet item")

    # Calcule le numéro global de la question (1-based)
    from config.iso42001_requirements import ISO42001_REQUIREMENTS
    req_order = { req["control_id"]: i for i, req in enumerate(ISO42001_REQUIREMENTS) }
    # récupère tous les items triés par control_id
    items = sess.exec(select(ISO42001ChecklistItem)
                      .where(ISO42001ChecklistItem.project_id == project_id)).all()
    items_sorted = sorted(items, key=lambda it: req_order.get(it.control_id, float("inf")))
    offset = 0
    for it in items_sorted:
        if it.id == item_id:
            break
        offset += len(it.audit_questions)
    global_number = offset + question_index + 1

    # Chemin vers le doc vierge
    base_dir = FSPath(__file__).resolve().parents[2]
    docs_dir = base_dir / "config" / "documents"
    filename = f"{global_number}.docx"
    file_path = docs_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )

# List NonConformites for a checklist item
@router.get(
    "/{project_id}/checklist/{item_id}/nonconformites",
    response_model=List[NonConformiteRead],
)
def list_nonconformites(
    team_id: int,
    project_id: int,
    item_id: int,
    question_index: int = Query(..., ge=0),  # <- nouveau paramètre obligatoire
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    verify_access(team_id, project_id, item_id, current_user, sess)

    ncs = sess.exec(
        select(NonConformite)
        .where(
            NonConformite.checklist_item_id == item_id,
            NonConformite.question_index == question_index
        )
    ).all()

    return ncs



# Update a NonConformite
@router.put(
    "/{project_id}/checklist/{item_id}/nonconformites/{nc_id}",
    response_model=NonConformiteRead,
)
def update_nonconformite(
    team_id: int,
    project_id: int,
    item_id: int,
    nc_id: int,
    payload: NonConformiteUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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


# Delete a NonConformite
@router.delete(
    "/{project_id}/checklist/{item_id}/nonconformites/{nc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_nonconformite(
    team_id: int,
    project_id: int,
    item_id: int,
    nc_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    verify_access(team_id, project_id, item_id, current_user, sess)

    nc = sess.get(NonConformite, nc_id)
    if not nc or nc.checklist_item_id != item_id:
        raise HTTPException(status_code=404, detail="NonConformite not found")

    sess.delete(nc)
    sess.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

class NonConformityNotification(BaseModel):
    id: int
    deadline_correction: Optional[datetime]
    statut: str
    checklist_item_id: int
    question_index: int

    class Config:
        orm_mode = True

@router.get(
    "/{project_id}/notifications/nonconformities",
    response_model=List[NonConformityNotification],
    summary="Liste des alertes de non-conformités majeures non corrigées proches/dépassant deadline"
)
def get_nc_notifications(
    team_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session)
):
    # Vérifier que user appartient à l'équipe
    membership = sess.exec(
        select(TeamMembership)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == current_user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Accès interdit à cette équipe")

    # Vérifier que le projet appartient à l'équipe
    proj = sess.get(AIProject, project_id)
    if not proj or proj.team_id != team_id:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    now = datetime.utcnow()
    soon = now + timedelta(days=7)

    # Sélectionner les NC majeures non corrigées proches/dépassant deadline
    ncs = sess.exec(
        select(NonConformite)
        .join(NonConformite.checklist_item)  # relier à checklist item
        .where(
            NonConformite.type_nc == "majeure",
            NonConformite.statut != "corrigee",
            NonConformite.deadline_correction != None,
            NonConformite.deadline_correction <= soon,
            # Vérifier que le checklist item appartient au projet
            NonConformite.checklist_item.has(project_id=project_id),
        )
        .order_by(NonConformite.deadline_correction)
    ).all()

    return ncs