# app/routers/documents.py
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import List, Dict
import io, uuid

from PIL import Image
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
    Response,
    Form,
)
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, delete

from app.db import SessionLocal
from app.models import (
    Document,
    DocumentCreate,
    DocumentRead,
    DocumentHistory,
    DocumentImage,
    TeamMembership,
)
from app.auth import get_current_user, User
from app.utils.pdf import pdf_to_markdown_and_images, markdown_to_pdf

router = APIRouter(prefix="/teams/{team_id}/documents", tags=["team-documents"])


# ──────────────────────────── helpers ──────────────────────────────
def _assert_member(sess: Session, team_id: int, user: User):
    """Vérifie que l’utilisateur est membre (invitation acceptée) de l’équipe."""
    mem = sess.exec(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id,
            TeamMembership.accepted_at.is_not(None),
        )
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Accès interdit à cette équipe")


def _assert_doc_team(doc: Document, team_id: int):
    if doc.team_id != team_id:
        raise HTTPException(status_code=404, detail="Document not found")


# ───────────────────────────── CRUD docs ───────────────────────────
@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    team_id: int,
    payload: DocumentCreate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)

        doc = Document(
            title=payload.title,
            content=payload.content,
            created_by=current_user.username,
            team_id=team_id,
        )
        sess.add(doc)
        sess.commit()
        sess.refresh(doc)

        sess.add(
            DocumentHistory(
                document_id=doc.id,
                title=doc.title,
                content=doc.content,
                version=doc.version,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                created_by=doc.created_by,
            )
        )
        sess.commit()
        return DocumentRead.from_orm(doc)


@router.post("/upload-pdf", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    team_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF uploads supported")

    pdf_bytes = await file.read()
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)

        doc = Document(
            title=file.filename,
            content="",
            created_by=current_user.username,
            team_id=team_id,
        )
        sess.add(doc)
        sess.flush()  # récupère doc.id

        doc.content = pdf_to_markdown_and_images(pdf_bytes, sess, doc)
        sess.commit()
        sess.refresh(doc)

        sess.add(
            DocumentHistory(
                document_id=doc.id,
                title=doc.title,
                content=doc.content,
                version=doc.version,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                created_by=doc.created_by,
            )
        )
        sess.commit()
        return DocumentRead.from_orm(doc)


@router.get("/", response_model=List[DocumentRead])
def list_documents(
    team_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        docs = sess.exec(select(Document).where(Document.team_id == team_id)).all()
        return [DocumentRead.from_orm(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentRead)
def read_document(
    team_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        doc = sess.get(Document, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        _assert_doc_team(doc, team_id)
        return DocumentRead.from_orm(doc)


@router.get("/{doc_id}/images/{img_id}")
def get_image(
    team_id: int,
    doc_id: int,
    img_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        img = sess.get(DocumentImage, img_id)
        if not img or img.document_id != doc_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
        # doc.team_id is implicitly correct because FK chain
        return Response(content=img.data, media_type=img.mime_type)


@router.get("/{doc_id}/download-pdf")
def download_pdf(
    team_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        doc = sess.get(Document, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        _assert_doc_team(doc, team_id)

        pdf_bytes = markdown_to_pdf(doc.content, title=doc.title)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{doc.title}.pdf"'},

    )


@router.put("/{doc_id}", response_model=DocumentRead)
def update_document(
    team_id: int,
    doc_id: int,
    payload: DocumentCreate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        doc = sess.get(Document, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        _assert_doc_team(doc, team_id)

        doc.title = payload.title
        doc.content = payload.content
        doc.version += 1
        doc.updated_at = datetime.utcnow()
        sess.add(doc)
        sess.commit()
        sess.refresh(doc)

        sess.add(
            DocumentHistory(
                document_id=doc.id,
                title=doc.title,
                content=doc.content,
                version=doc.version,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                created_by=doc.created_by,
            )
        )
        sess.commit()
        return DocumentRead.from_orm(doc)


@router.get("/{doc_id}/history", response_model=List[DocumentHistory])
def history_document(
    team_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        rows = sess.exec(
            select(DocumentHistory)
            .where(DocumentHistory.document_id == doc_id)
            .order_by(DocumentHistory.version)
        ).all()
        return [DocumentHistory.from_orm(r) for r in rows]


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    team_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        doc = sess.get(Document, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        _assert_doc_team(doc, team_id)

        sess.exec(delete(DocumentHistory).where(DocumentHistory.document_id == doc_id))
        sess.exec(delete(DocumentImage).where(DocumentImage.document_id == doc_id))
        sess.delete(doc)
        sess.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{doc_id}/images", status_code=status.HTTP_201_CREATED, response_model=Dict[str, int])
async def upload_document_image(
    team_id: int,
    doc_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    data = await file.read()
    mime = file.content_type or "application/octet-stream"
    filename = file.filename

    if mime.lower() not in ("image/png",):
        buf_in = io.BytesIO(data)
        pil = Image.open(buf_in).convert("RGBA")
        buf_out = io.BytesIO()
        pil.save(buf_out, format="PNG")
        data = buf_out.getvalue()
        mime = "image/png"
        filename = f"{uuid.uuid4().hex}.png"

    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)

        doc = sess.get(Document, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        _assert_doc_team(doc, team_id)

        img = DocumentImage(
            document_id=doc_id,
            filename=filename,
            mime_type=mime,
            data=data,
        )
        sess.add(img)
        sess.commit()
        sess.refresh(img)
        return {"id": img.id}
