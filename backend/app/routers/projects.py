from datetime import datetime
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
    Proof,
)
from config.iso42001_requirements import ISO42001_REQUIREMENTS

router = APIRouter(prefix="/projects", tags=["projects"])


def get_session():
    with SessionLocal() as sess:
        yield sess


# ─────────────────────────── PROJECT CRUD ────────────────────────────────────
@router.post("/", response_model=AIProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: AIProjectCreate,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = AIProject.from_orm(payload)
    proj.owner = current_user.username
    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return proj


@router.get("/", response_model=List[AIProjectRead])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(6, gt=0, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    query = select(AIProject)
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
    return sess.exec(query.offset(skip).limit(limit)).all()


@router.get("/{project_id}", response_model=AIProjectRead)
def read_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    sess.refresh(proj)
    return proj


@router.put("/{project_id}", response_model=AIProjectRead)
def update_project(
    project_id: int,
    payload: AIProjectCreate,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
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
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    # 1) Récupère tous les checklist_item_ids du projet
    item_ids = sess.exec(
        select(ISO42001ChecklistItem.id)
        .where(ISO42001ChecklistItem.project_id == project_id)
    ).all()

    if item_ids:
        # 2) Supprime d'abord les actions correctives
        sess.exec(
            delete(ActionCorrective)
            .where(ActionCorrective.checklist_item_id.in_(item_ids))
        )
        # 3) Supprime **toutes** les preuves liées
        sess.exec(
            delete(Proof)
            .where(Proof.checklist_item_id.in_(item_ids))
        )
        # 4) Supprime ensuite les checklist items
        sess.exec(
            delete(ISO42001ChecklistItem)
            .where(ISO42001ChecklistItem.project_id == project_id)
        )

    # 5) Enfin, supprime le projet lui-même
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    sess.delete(proj)
    sess.commit()


# ───────────────────────────── COMMENTS ──────────────────────────────────────
@router.get("/{project_id}/comments", response_model=List[Comment])
def list_comments(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    sess.refresh(proj)
    return proj.comments


@router.post("/{project_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_comment(
    project_id: int,
    payload: CommentCreate = Body(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    comment = Comment(author=current_user.username, content=payload.content)
    proj.comments = proj.comments + [comment.dict()]
    proj.updated_at = datetime.utcnow()
    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return comment


@router.put("/{project_id}/comments/{comment_id}", response_model=Comment)
def update_comment(
    project_id: int,
    comment_id: str = Path(...),
    payload: CommentCreate = Body(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    for c in proj.comments:
        if isinstance(c, dict) and c["id"] == comment_id:
            c["content"] = payload.content
            c["date"] = datetime.utcnow().isoformat()
            break
    else:
        raise HTTPException(status_code=404, detail="Comment not found")
    proj.updated_at = datetime.utcnow()
    sess.add(proj)
    sess.commit()
    sess.refresh(proj)
    return next(filter(lambda x: x["id"] == comment_id, proj.comments))


@router.delete("/{project_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    project_id: int,
    comment_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    before = len(proj.comments)
    proj.comments = [
        c for c in proj.comments
        if not (isinstance(c, dict) and c["id"] == comment_id)
    ]
    if len(proj.comments) == before:
        raise HTTPException(status_code=404, detail="Comment not found")
    proj.updated_at = datetime.utcnow()
    sess.add(proj)
    sess.commit()


# ─────────────────────────── CHECKLIST ITEMS ────────────────────────────────
@router.get(
    "/{project_id}/checklist",
    response_model=List[ISO42001ChecklistItem],
    summary="Liste complète des items (avec leurs tableaux `statuses` et `results`)"
)
def list_checklist_items(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    project_id: int,
    item: ISO42001ChecklistItem,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    project_id: int,
    item_id: int,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
    if "result" in payload:
        item.results[idx] = payload["result"]
    if "observation" in payload:
        item.observations[idx] = payload["observation"]

    item.updated_at = datetime.utcnow()
    sess.add(item)
    sess.commit()
    sess.refresh(item)
    return item


# ─────────────────────── CORRECTIVE ACTIONS ─────────────────────────────────
@router.post("/{project_id}/checklist/{item_id}/actions", response_model=ActionCorrective)
def create_action_corrective(
    project_id: int,
    item_id: int,
    action: ActionCorrective,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    corrective_action = ActionCorrective(
        description=action.description,
        deadline=action.deadline,
        status="In Progress",
        checklist_item_id=item_id,
    )
    sess.add(corrective_action)
    sess.commit()
    sess.refresh(corrective_action)
    return corrective_action


@router.put("/{project_id}/checklist/{item_id}/actions/{action_id}", response_model=ActionCorrective)
def update_action_corrective(
    project_id: int,
    item_id: int,
    action_id: int,
    action: ActionCorrective,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    corrective_action = sess.get(ActionCorrective, action_id)
    if not corrective_action or corrective_action.checklist_item_id != item_id:
        raise HTTPException(status_code=404, detail="Action corrective not found")
    corrective_action.description = action.description
    corrective_action.deadline = action.deadline
    corrective_action.status = action.status
    corrective_action.updated_at = datetime.utcnow()
    sess.add(corrective_action)
    sess.commit()
    sess.refresh(corrective_action)
    return corrective_action


@router.get("/{project_id}/checklist/{item_id}/actions", response_model=List[ActionCorrective])
def get_actions_for_item(
    project_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return sess.exec(
        select(ActionCorrective).where(ActionCorrective.checklist_item_id == item_id)
    ).all()


@router.delete("/{project_id}/checklist/{item_id}/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_corrective(
    project_id: int,
    item_id: int,
    action_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    item = sess.get(ISO42001ChecklistItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    action = sess.get(ActionCorrective, action_id)
    if not action or action.checklist_item_id != item_id:
        raise HTTPException(status_code=404, detail="Action corrective not found")
    sess.delete(action)
    sess.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ────────────────────────────── PROOFS (evidence) ─────────────────────────────
@router.post(
    "/{project_id}/checklist/{item_id}/proofs",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
    summary="Upload ou mise à jour d'une preuve associée à un evidence_id"
)
async def upload_proof(
    project_id: int,
    item_id: int,
    evidence_id: str = Form(...),   # identifiant de la preuve
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
        "download_url": f"/projects/{project_id}/proofs/{proof.id}"
    }

@router.get(
    "/{project_id}/checklist/{item_id}/questions/{question_index}/proofs",
    response_model=List[Dict[str, Any]],
    summary="Liste les preuves pour une question donnée"
)
def list_proofs_for_question(
    project_id: int,
    item_id: int,
    question_index: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
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
            "download_url": f"/projects/{project_id}/proofs/{p.id}",
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