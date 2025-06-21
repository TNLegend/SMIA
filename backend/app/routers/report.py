import os
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
# pdfkit est une librairie Python qui sert d'interface à l'outil en ligne de commande wkhtmltopdf.
import pdfkit
# Ces fonctions sont définies ailleurs et servent à récupérer les données et à générer le HTML.
from app.utils.report_generator import get_audit_data_for_project, get_risk_analysis_for_project, generate_report_html

# BLOC D'INITIALISATION DU ROUTER
# Le router est configuré pour toutes les routes liées aux rapports d'une équipe.
router = APIRouter(prefix="/teams/{team_id}/reports", tags=["reports"])


@router.get("/{project_id}/audit-risk-report.pdf")
def get_audit_risk_report_pdf(team_id: int, project_id: int):
    """
    team_id est ici reçu mais non utilisé côté logique métier,
    il sert surtout à matcher l’URL et à respecter la structure REST.
    """
    # BLOC DE GÉNÉRATION DU RAPPORT PDF D'AUDIT ET DE RISQUES
    # Cette fonction est un pipeline complet pour créer un rapport PDF à la demande.
    # 1.  Configuration de l'outil : Elle configure `pdfkit` pour utiliser un exécutable
    #     spécifique de `wkhtmltopdf`, qui est l'outil qui effectue la conversion de HTML en PDF.
    #     Le chemin est codé en dur, ce qui suppose un déploiement contrôlé.
    # 2.  Collecte des données : Elle appelle des fonctions externes (`get_audit_data...`,
    #     `get_risk_analysis...`) pour rassembler toutes les informations nécessaires au rapport.
    # 3.  Génération du HTML : Ces données sont passées à `generate_report_html` qui
    #     construit une page HTML complète représentant le rapport.
    # 4.  Conversion en PDF : `pdfkit.from_string` prend le HTML généré et le convertit
    #     en une séquence d'octets (bytes) représentant le fichier PDF.
    # 5.  Envoi de la réponse : Elle retourne une `Response` FastAPI contenant les bytes du PDF,
    #     avec le type de média approprié et un en-tête `Content-Disposition` qui
    #     indique au navigateur de télécharger le fichier avec un nom spécifique.
    #
    # Note de sécurité importante : Cette route ne contient actuellement aucune vérification
    # d'authentification ou d'autorisation. N'importe qui connaissant un `project_id` valide
    # pourrait potentiellement générer un rapport. L'ajout d'un contrôle d'accès est recommandé.

    # Chemin vers wkhtmltopdf (suppose un environnement Windows/WSL)
    WKHTMLTOPDF_PATH = os.path.join(
        os.getcwd(), "app", "utils", "wkhtmltopdf", "bin", "wkhtmltopdf.exe"
    )
    if not os.path.isfile(WKHTMLTOPDF_PATH):
        raise RuntimeError(f"Cannot find wkhtmltopdf at {WKHTMLTOPDF_PATH}")
    PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

    try:
        print("got it")
        audit_data = get_audit_data_for_project(project_id)
        risk_data = get_risk_analysis_for_project(project_id)
        report_html = generate_report_html(audit_data, risk_data)

        # Conversion du HTML en bytes PDF sans passer par un fichier temporaire.
        pdf_bytes = pdfkit.from_string(report_html, False, configuration=PDFKIT_CONFIG)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=rapport_projet_{project_id}.pdf"
            },
        )
    except Exception as e:
        # En cas d'erreur, affiche la trace dans la console et retourne une exception HTTP.
        # Une erreur 500 (Internal Server Error) serait peut-être plus appropriée qu'une 404.
        traceback.print_tb(e.__traceback__)
        raise HTTPException(status_code=404, detail=str(e))