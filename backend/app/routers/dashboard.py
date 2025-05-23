from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Dict, Any, List
from app.db import SessionLocal
from app.models import (
    Team, AIProject, NonConformite,
    EvaluationRun, ActionCorrective, Comment
)
from app.auth import get_current_user, User
import datetime

router = APIRouter()

@router.get("/teams/{team_id}/dashboard/full_summary")
def full_dashboard_summary(team_id: int, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    with SessionLocal() as sess:
        # Vérification existence équipe
        team = sess.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Équipe non trouvée")

        # Vérification que user est membre actif
        if not any(m.user_id == current_user.id and m.accepted_at for m in team.members):
            raise HTTPException(403, "Accès interdit : pas membre de l'équipe")

        # Récupérer projets de l'équipe
        projects: List[AIProject] = sess.exec(
            select(AIProject).where(AIProject.team_id == team_id)
        ).all()
        total_projects = len(projects)

        compliance_scores = []
        compliance_details = []

        # Calcul conformité au niveau des questions
        for p in projects:
            total_questions = 0
            compliant_questions = 0

            for item in p.checklist_items:
                statuses = item.results or []
                print(statuses)
                # On vérifie chaque question dans les statuses associés
                for status in statuses:
                    total_questions += 1
                    print(status)
                    if status == "compliant":
                        print("done")
                        compliant_questions += 1
            print("compliant" + str(compliant_questions))
            print("total" + str(total_questions))
            score = round(float((compliant_questions / total_questions) * 100), 3) if total_questions > 0 else 0
            compliance_scores.append(score)

            compliance_details.append({
                "project_id": p.id,
                "project_title": p.title,
                "description": p.description or "",
                "category": p.category or "Non défini",
                "owner": p.owner or "Inconnu",
                "createdAt": p.created_at.isoformat(),
                "status": p.status or "active",
                "riskLevel": "medium",  # Valeur par défaut si non renseignée
                "compliance_score": score,
                "total_questions": total_questions,
                "conform_questions": compliant_questions
            })

        average_compliance = round(sum(compliance_scores) / len(compliance_scores), 3) if compliance_scores else 0

        # Comptage des non-conformités majeures non corrigées
        major_nc_count = 0
        for p in projects:
            for item in p.checklist_items:
                major_nc_count += sum(
                    1 for nc in item.non_conformites
                    if nc.type_nc.lower() == "majeure" and nc.statut.lower() != "corrigee"
                )

        # Actions correctives ouvertes ou en cours (status francais et anglais possibles)
        open_actions = sess.exec(
            select(ActionCorrective)
            .where(ActionCorrective.status.in_([
                "to-do", "in-progress", "in-review",
                "non_corrigee", "non corrigée", "non corrigé", "non_corrigée",
                "ouverte", "en_cours", "en cours"
            ]))
        ).all()
        open_actions_count = len(open_actions)

        # Dernières évaluations IA par projet
        evaluation_summaries = []
        for p in projects:
            last_eval = sess.exec(
                select(EvaluationRun)
                .where(EvaluationRun.project_id == p.id)
                .order_by(EvaluationRun.created_at.desc())
            ).first()

            if last_eval:
                evaluation_summaries.append({
                    "project_id": p.id,
                    "project_title": p.title,
                    "evaluation_date": last_eval.created_at.isoformat(),
                    "status": last_eval.status,
                    "metrics": last_eval.metrics,
                })
            else:
                evaluation_summaries.append({
                    "project_id": p.id,
                    "project_title": p.title,
                    "evaluation_date": None,
                    "status": "non évalué",
                    "metrics": {}
                })

        # 5 derniers commentaires récents pour l'équipe
        query = (
            select(Comment)
            .join(AIProject, Comment.project_id == AIProject.id)
            .where(AIProject.team_id == team_id)
            .order_by(Comment.date.desc())
            .limit(5)  # Limite ici avant exec
        )
        recent_comments = sess.exec(query).all()

        recent_comments_list = [{
            "comment_id": c.id,
            "project_id": c.project_id,
            "author": c.author,
            "content": c.content,
            "date": c.date.isoformat(),
        } for c in recent_comments]

        # Construire la réponse
        response = {
            "team_id": team.id,
            "team_name": team.name,
            "total_projects": total_projects,
            "average_compliance_iso42001": average_compliance,
            "compliance_details": compliance_details,
            "major_nonconformities_count": major_nc_count,
            "open_actions_correctives_count": open_actions_count,
            "evaluations": evaluation_summaries,
            "recent_comments": recent_comments_list,
        }

        return response
