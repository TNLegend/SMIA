# app/utils/report_generator.py

from typing import Dict, Any
from sqlmodel import Session, select
from app.db import SessionLocal
from app.models import (
    AIProject,
    ISO42001ChecklistItem,
    EvaluationRun,
)

def get_audit_data_for_project(project_id: int) -> Dict[str, Any]:
    with SessionLocal() as sess:
        project = sess.get(AIProject, project_id)
        if not project:
            raise ValueError(f"Projet {project_id} introuvable")

        checklist_items = []
        for item in project.checklist_items:
            questions_data = []
            for idx, question in enumerate(item.audit_questions):
                # Preuves liées à cette question
                proofs_for_question = [
                    {
                        "filename": proof.filename,
                        "proof_id": proof.id,
                        "checklist_item_id": proof.checklist_item_id,
                        "evidence_id": proof.evidence_id,
                    }
                    for proof in item.proofs
                    if proof.evidence_id in question.get("evidence_refs", [])
                ]

                # Non-conformités liées à cette question
                ncs_for_question = []
                for nc in item.non_conformites:
                    if nc.question_index == idx:
                        actions_for_nc = [
                            {
                                "description": action.description,
                                "responsible": getattr(action.responsible_user, "username", "?") if action.responsible_user else "?",
                                "deadline": action.deadline.isoformat() if action.deadline else None,
                                "status": action.status,
                            }
                            for action in nc.actions_correctives
                        ]

                        ncs_for_question.append({
                            "id": nc.id,
                            "type_nc": nc.type_nc.value if hasattr(nc.type_nc, "value") else nc.type_nc,
                            "statut": nc.statut.value if hasattr(nc.statut, "value") else nc.statut,
                            "deadline_correction": nc.deadline_correction.isoformat() if nc.deadline_correction else None,
                            "actions_correctives": actions_for_nc,
                        })

                questions_data.append({
                    "question": question.get("question", ""),
                    "status": item.statuses[idx] if idx < len(item.statuses) else "",
                    "result": item.results[idx] if idx < len(item.results) else "",
                    "observation": item.observations[idx] if idx < len(item.observations) else "",
                    "evidence_required": item.evidence_required,
                    "proofs": proofs_for_question,
                    "non_conformities": ncs_for_question,
                })

            checklist_items.append({
                "control_id": item.control_id,
                "control_name": item.control_name,
                "description": item.description,
                "status": item.status,
                "result": item.result,
                "observation": item.observation,
                "audit_questions": questions_data,
            })

        # Récupérer les membres de l'équipe via la relation "team" du projet
        team_members = []
        if project.team and project.team.members:
            for membership in project.team.members:
                if membership.user:
                    team_members.append({"username": membership.user.username})

        return {
            "project_title": project.title,
            "description": project.description or "",
            "team_members": team_members,
            "checklist_items": checklist_items,
        }


def get_risk_analysis_for_project(project_id: int) -> Dict[str, Any]:
    with SessionLocal() as sess:
        eval_run = sess.exec(
            select(EvaluationRun)
            .where(EvaluationRun.project_id == project_id)
            .order_by(EvaluationRun.created_at.desc())
        ).first()
        if not eval_run:
            return {}

        return eval_run.metrics or {}


def generate_report_html(audit_data: Dict[str, Any], risk_analysis_data: Dict[str, Any]) -> str:
    # HTML + CSS complet, moderne et lisible
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<title>Rapport d’Audit et d’Analyse des Risques IA</title>
<style>
  body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 30px;
    color: #222;
    background: #f9f9f9;
  }}
  h1, h2, h3, h4 {{
    color: #004d99;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 25px;
  }}
  th, td {{
    border: 1px solid #ccc;
    padding: 10px;
    text-align: left;
  }}
  th {{
    background-color: #e6f0ff;
  }}
  tr:nth-child(even) {{
    background-color: #f2faff;
  }}
  .section-separator {{
    border-top: 3px solid #004d99;
    margin: 40px 0 30px 0;
  }}
  ul {{
    margin: 10px 0 20px 20px;
  }}
  .small-text {{
    font-size: 0.9em;
    color: #555;
  }}
  .nc-actions {{
    margin-left: 15px;
  }}
</style>
</head>
<body>

<h1>Rapport d’Audit et d’Analyse des Risques IA</h1>

<h2>1. Introduction</h2>
<p><strong>Projet :</strong> {audit_data['project_title']}</p>
<p><strong>Description :</strong> {audit_data.get('description', 'Non spécifiée')}</p>

<div class="section-separator"></div>

<h2>2. Résultats de l’Audit Organisationnel (ISO 42001)</h2>
"""

    for item in audit_data["checklist_items"]:
        html += f"""
<h3>{item['control_id']} - {item['control_name']}</h3>
<p><strong>Description :</strong> {item['description']}</p>
<p><strong>Statut global :</strong> {item.get('status', '')} | <strong>Résultat global :</strong> {item.get('result', '')}</p>
"""
        if item.get('observation'):
            html += f"<p><strong>Observation globale :</strong> {item.get('observation')}</p>"

        # Questions détaillées
        for idx, question in enumerate(item.get("audit_questions", []), start=1):
            html += f"""
<h4>Question {idx}: {question.get('question', '')}</h4>
<ul>
  <li><strong>Statut :</strong> {question.get('status', '')}</li>
  <li><strong>Résultat :</strong> {question.get('result', '')}</li>"""
            if question.get('observation'):
                html += f"<li><strong>Observation :</strong> {question.get('observation')}</li>"
            # Preuves
            proofs = question.get('proofs', [])
            if proofs:
                html += "<li><strong>Preuves associées :</strong><ul>"
                for proof in proofs:
                    html += f"<li>{proof['filename']}</li>"
                html += "</ul></li>"
            # Non-conformités et actions
            ncs = question.get('non_conformities', [])
            if ncs:
                html += "<li><strong>Non-conformités associées :</strong><ul>"
                for nc in ncs:
                    html += f"""
<li>
Type : {nc.get('type_nc','')} | Statut : {nc.get('statut','')} | Deadline : {nc.get('deadline_correction', 'N/A')}
"""
                    actions = nc.get('actions_correctives', [])
                    if actions:
                        html += "<ul class='nc-actions'>"
                        for action in actions:
                            html += f"<li>{action['description']} (Responsable : {action.get('responsible','?')}, Deadline : {action.get('deadline')}, Statut : {action.get('status')})</li>"
                        html += "</ul>"
                    html += "</li>"
                html += "</ul></li>"
            html += "</ul>"

        html += '<hr style="margin:40px 0;">'

    # Analyse technique risques IA
    html += """
<div class="section-separator"></div>
<h2>3. Analyse Technique des Risques IA</h2>

<h3>3.1 Performance du modèle</h3>
<ul>
"""
    performance = risk_analysis_data.get("performance", {})
    if performance:
        for k, v in performance.items():
            html += f"<li><strong>{k} :</strong> {v:.4f}</li>"
    else:
        html += "<li>Aucune donnée de performance disponible.</li>"
    html += "</ul>"

    # Fairness / Equité
    html += "<h3>3.2 Équité et biais</h3>"
    fairness = risk_analysis_data.get("fairness", {})
    if fairness:
        for attr, metrics in fairness.items():
            html += f"<h4>Attribut sensible : {attr}</h4><ul>"
            for metric_name, metric_val in metrics.items():
                html += f"<li>{metric_name}: {metric_val}</li>"
            html += "</ul>"
    else:
        html += "<p>Aucune donnée d’équité disponible.</p>"

    # Drift / Dérive
    html += "<h3>3.3 Dérive des données</h3><ul>"
    drift = risk_analysis_data.get("drift", {})
    if drift:
        for test_name, val in drift.items():
            html += f"<li>{test_name} : {val}</li>"
    else:
        html += "<li>Aucune donnée de dérive disponible.</li>"
    html += "</ul>"

    # Robustesse
    html += "<h3>3.4 Robustesse</h3><ul>"
    robustness = risk_analysis_data.get("robustness", {})
    if robustness:
        for k, v in robustness.items():
            html += f"<li>{k}: {v}</li>"
    else:
        html += "<li>Aucune donnée de robustesse disponible.</li>"
    html += "</ul>"

    # Synthèse & recommandations
    html += """
<div class="section-separator"></div>
<h2>4. Synthèse & Recommandations</h2>
<p>(À compléter selon contexte et analyses)</p>

<h2>5. Annexes</h2>
<p>Données brutes et fichiers annexes.</p>

</body>
</html>"""

    return html
