import os
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import pdfkit
from app.utils.report_generator import get_audit_data_for_project, get_risk_analysis_for_project, generate_report_html

router = APIRouter(prefix="/teams/{team_id}/reports", tags=["reports"])

@router.get("/{project_id}/audit-risk-report.pdf")
def get_audit_risk_report_pdf(team_id: int, project_id: int):
    """
    team_id est ici reçu mais non utilisé côté logique métier,
    il sert surtout à matcher l’URL et à respecter la structure REST.
    """
    # Chemin vers wkhtmltopdf (Windows/WSL)
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
        pdf_bytes = pdfkit.from_string(report_html, False, configuration=PDFKIT_CONFIG)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=rapport_projet_{project_id}.pdf"
            },
        )
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        raise HTTPException(status_code=404, detail=str(e))
