# Utilities to convert PDFs to markdown and back
import os
import re
import base64
import uuid

import fitz      # PyMuPDF
import markdown
import pdfkit
from sqlmodel import Session

from app.db import SessionLocal
from app.models import DocumentImage

# ─────────────────────────────────────────────────────────────────────────────
# Chemin vers wkhtmltopdf (Windows/WSL)
WKHTMLTOPDF_PATH = os.path.join(
    os.getcwd(), "app", "utils", "wkhtmltopdf", "bin", "wkhtmltopdf.exe"
)
if not os.path.isfile(WKHTMLTOPDF_PATH):
    raise RuntimeError(f"Cannot find wkhtmltopdf at {WKHTMLTOPDF_PATH}")
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
# ─────────────────────────────────────────────────────────────────────────────


def pdf_to_markdown_and_images(pdf_bytes: bytes, sess: Session, doc) -> str:
    """
    • Extrait texte & images d’un PDF.
    • Stocke chaque image en PNG dans DocumentImage.
    • Retourne du Markdown pointant vers /documents/{doc.id}/images/{img.id}.
    """
    md_chunks: list[str] = []
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")

    for pno, page in enumerate(pdf, start=1):
        txt = page.get_text("text")
        if txt.strip():
            md_chunks.append(txt.strip())

        for idx, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            pix = fitz.Pixmap(pdf, xref)
            png = pix.tobytes("png")
            pix = None

            img_row = DocumentImage(
                document_id=doc.id,
                filename   = f"{uuid.uuid4().hex}.png",
                mime_type  = "image/png",
                data       = png
            )
            sess.add(img_row)
            sess.flush()  # récupère img_row.id

            md_chunks.append(
                f"![page-{pno}-img-{idx}](/documents/{doc.id}/images/{img_row.id})"
            )

        md_chunks.append("")  # saut de ligne entre pages

    return "\n\n".join(md_chunks)


def markdown_to_pdf(md: str, title: str | None = None) -> bytes:
    """
    • Convertit Markdown → HTML fragment.
    • Remplace chaque <img src="/documents/.../images/N"...> par une balise
      <img src="data:<mime>;base64,..." alt="..." style="..."/> intégrée.
    • Génère le PDF via wkhtmltopdf.
    """
    # 1) Markdown → fragment HTML
    body_html = markdown.markdown(
        md,
        extensions=["extra", "toc", "tables", "fenced_code"]
    )
    if title:
        body_html = f"<h1>{title}</h1>\n" + body_html

    # 2) Regex pour capturer tout <img src="/documents/.../images/N" …>
    IMG_RE = re.compile(
        r'<img\s+[^>]*src=["\'](?P<src>/documents/\d+/images/(?P<img_id>\d+))["\'][^>]*>',
        flags=re.IGNORECASE
    )

    def _embed(match: re.Match[str]) -> str:
        orig_tag = match.group(0)
        img_id   = int(match.group("img_id"))

        # On re-ouvre une session pour récupérer le BLOB
        with SessionLocal() as sess:
            img = sess.get(DocumentImage, img_id)

        if not img:
            return orig_tag  # si introuvable, on ne change rien

        # Détection JPEG via signature binaire
        data_bytes = img.data
        if data_bytes[:2] == b'\xff\xd8':
            mime = "image/jpeg"
        else:
            mime = img.mime_type  # ex: "image/png"

        b64 = base64.b64encode(data_bytes).decode("ascii")

        # Récupère l'attribut alt si présent
        alt_m = re.search(r'alt=["\']([^"\']*)["\']', orig_tag)
        alt_text = alt_m.group(1) if alt_m else ""

        # Reconstruction de la balise <img> embarquée
        return (
            f'<img '
            f'src="data:{mime};base64,{b64}" '
            f'alt="{alt_text}" '
            f'style="display:block;max-width:100%;height:auto;margin:1em 0;" '
            f'/>'
        )

    # 3) Injection de toutes les images en data-URI
    body_html = IMG_RE.sub(_embed, body_html)

    # 4) Enveloppe HTML complet
    full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>{title or ''}</title>
  <style>
    body {{ font-family: DejaVu Sans, Arial, sans-serif; margin:20px; }}
    pre  {{ white-space: pre-wrap; word-break: break-word; }}
    img  {{ display:block;max-width:100%;height:auto;margin:1em 0; }}
  </style>
</head>
<body>
{body_html}
</body>
</html>
"""

    # 5) Options wkhtmltopdf (ignore tout appel réseau)
    options = {
        "enable-local-file-access":    None,
        "encoding":                   "UTF-8",
        "margin-top":                 "15mm",
        "margin-bottom":              "15mm",
        "margin-left":                "15mm",
        "margin-right":               "15mm",
        "footer-right":               "[page] / [toPage]",
        "load-error-handling":        "ignore",
        "load-media-error-handling":  "ignore",
    }

    # 6) Génération et retour des octets PDF
    return pdfkit.from_string(
        full_html, False,
        configuration=PDFKIT_CONFIG,
        options=options
    )
