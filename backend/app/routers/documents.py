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
# Fonctions utilitaires pour la conversion de PDF
from app.utils.pdf import pdf_to_markdown_and_images, markdown_to_pdf

# BLOC 1 : CONFIGURATION ET FONCTIONS D'AIDE (HELPERS)
# Initialisation du router avec un préfixe commun et un tag pour la documentation.
router = APIRouter(prefix="/teams/{team_id}/documents", tags=["team-documents"])

def _assert_member(sess: Session, team_id: int, user: User):
    """Helper de sécurité : Vérifie que l'utilisateur courant est un membre actif de l'équipe."""
    mem = sess.exec(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id,
            TeamMembership.accepted_at.is_not(None), # L'invitation doit être acceptée
        )
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Accès interdit à cette équipe")

def _assert_doc_team(doc: Document, team_id: int):
    """Helper de validation : Vérifie que le document appartient bien à l'équipe spécifiée dans l'URL."""
    if doc.team_id != team_id:
        raise HTTPException(status_code=404, detail="Document not found")

# ───────────────────────── CRUD : Création de Documents ───────────────────────────

@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    team_id: int,
    payload: DocumentCreate, # Création à partir de données JSON (titre, contenu)
    current_user: User = Depends(get_current_user),
):
    # BLOC DE CRÉATION DE DOCUMENT STANDARD
    # Cette route crée un document à partir d'un titre et d'un contenu textuel.
    # 1. Vérifie les droits de l'utilisateur.
    # 2. Crée l'objet `Document` en base de données.
    # 3. Crée une première entrée dans la table `DocumentHistory` pour sauvegarder la version initiale.
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        doc = Document(
            title=payload.title, content=payload.content,
            created_by=current_user.username, team_id=team_id,
        )
        sess.add(doc)
        sess.commit()
        sess.refresh(doc)

        sess.add(DocumentHistory(
            document_id=doc.id, title=doc.title, content=doc.content,
            version=doc.version, created_at=doc.created_at,
            updated_at=doc.updated_at, created_by=doc.created_by,
        ))
        sess.commit()
        return DocumentRead.from_orm(doc)

@router.post("/upload-pdf", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    team_id: int,
    file: UploadFile = File(...), # Création à partir d'un fichier uploadé
    current_user: User = Depends(get_current_user),
):
    # BLOC DE CRÉATION DE DOCUMENT PAR IMPORT PDF
    # Cette route plus complexe gère l'upload d'un fichier PDF.
    # 1. Valide le type de fichier.
    # 2. Lit le contenu du PDF et le convertit en Markdown grâce à l'utilitaire `pdf_to_markdown_and_images`.
    #    Cette fonction extrait également les images et les sauvegarde dans la table `DocumentImage`.
    # 3. Crée le document et sa première entrée d'historique.
    if file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF uploads supported")
    pdf_bytes = await file.read()
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        doc = Document(
            title=file.filename, content="",
            created_by=current_user.username, team_id=team_id,
        )
        sess.add(doc)
        sess.flush()  # `flush` permet d'obtenir doc.id avant le commit final

        doc.content = pdf_to_markdown_and_images(pdf_bytes, sess, doc)
        sess.commit()
        sess.refresh(doc)
        sess.add(DocumentHistory(
            document_id=doc.id, title=doc.title, content=doc.content,
            version=doc.version, created_at=doc.created_at,
            updated_at=doc.updated_at, created_by=doc.created_by,
        ))
        sess.commit()
        return DocumentRead.from_orm(doc)

# ─────────────────── CRUD : Lecture de Documents et Images ─────────────────────

@router.get("/", response_model=List[DocumentRead])
def list_documents(
    team_id: int,
    current_user: User = Depends(get_current_user),
):
    # BLOC DE LISTAGE DES DOCUMENTS
    # Récupère et retourne la liste de tous les documents appartenant à l'équipe.
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
    # BLOC DE LECTURE D'UN DOCUMENT SPÉCIFIQUE
    # Récupère un document par son ID, après avoir vérifié les droits d'accès.
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        doc = sess.get(Document, doc_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        _assert_doc_team(doc, team_id) # Vérifie que le doc appartient bien à l'équipe
        return DocumentRead.from_orm(doc)

@router.get("/{doc_id}/images/{img_id}")
def get_image(
    team_id: int,
    doc_id: int,
    img_id: int,
    current_user: User = Depends(get_current_user),
):
    # BLOC DE RÉCUPÉRATION D'IMAGE
    # Cette route sert à afficher les images qui ont été extraites des PDF.
    # Elle retourne directement les données binaires de l'image avec le bon type MIME.
    with SessionLocal() as sess:
        _assert_member(sess, team_id, current_user)
        img = sess.get(DocumentImage, img_id)
        if not img or img.document_id != doc_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
        return Response(content=img.data, media_type=img.mime_type)

# ─────────────────── CRUD : Mise à Jour, Suppression et Autres Actions ───────────────────

@router.get("/{doc_id}/download-pdf")
def download_pdf(
    team_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
):
    # BLOC D'EXPORTATION D'UN DOCUMENT EN PDF
    # Cette route fait l'opération inverse de l'upload : elle prend le contenu
    # Markdown stocké en base de données et le convertit à la volée en un fichier PDF.
    # 1. Vérifie les droits et récupère le document.
    # 2. Utilise l'utilitaire `markdown_to_pdf` pour la conversion.
    # 3. Utilise `StreamingResponse` pour envoyer le fichier efficacement, sans le charger
    #    entièrement en mémoire. Le header `Content-Disposition` indique au navigateur
    #    de proposer le téléchargement du fichier avec un nom approprié.
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
    # BLOC DE MISE À JOUR D'UN DOCUMENT (VERSIONING)
    # Met à jour le titre et le contenu d'un document existant.
    # 1. Vérifie les droits et récupère le document.
    # 2. Applique les modifications du `payload`.
    # 3. Incrémente le numéro de version du document.
    # 4. Crée une nouvelle entrée dans `DocumentHistory` pour archiver cette nouvelle version.
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

        sess.add(DocumentHistory(
            document_id=doc.id, title=doc.title, content=doc.content,
            version=doc.version, created_at=doc.created_at,
            updated_at=doc.updated_at, created_by=doc.created_by,
        ))
        sess.commit()
        return DocumentRead.from_orm(doc)


@router.get("/{doc_id}/history", response_model=List[DocumentHistory])
def history_document(
    team_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
):
    # BLOC DE LECTURE DE L'HISTORIQUE D'UN DOCUMENT
    # Récupère toutes les versions archivées d'un document depuis la table
    # `DocumentHistory`, ordonnées par numéro de version.
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
    # BLOC DE SUPPRESSION D'UN DOCUMENT ET DE SES DONNÉES LIÉES
    # Supprime un document de manière complète.
    # 1. Vérifie les droits et récupère le document.
    # 2. Effectue une "suppression en cascade" manuelle :
    #    - Supprime toutes les entrées d'historique associées.
    #    - Supprime toutes les images associées.
    #    - Supprime le document lui-même.
    # 3. Retourne une réponse 204 (No Content), pratique standard pour un DELETE réussi.
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
    # BLOC D'UPLOAD MANUEL D'IMAGE POUR UN DOCUMENT
    # Permet d'ajouter une image à un document existant (par exemple, pour l'insérer
    # dans le contenu Markdown).
    # 1. Lit le fichier uploadé.
    # 2. Intègre une logique de standardisation : si l'image n'est pas un PNG,
    #    elle est convertie en PNG à l'aide de la bibliothèque Pillow (PIL).
    #    Ceci assure que toutes les images stockées ont un format uniforme.
    # 3. Sauvegarde l'image (ses données binaires) dans la table `DocumentImage`.
    # 4. Retourne l'ID de la nouvelle image créée.
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
            document_id=doc_id, filename=filename, mime_type=mime, data=data,
        )
        sess.add(img)
        sess.commit()
        sess.refresh(img)
        return {"id": img.id}
