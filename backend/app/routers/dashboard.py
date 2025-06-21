from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Dict, Any, List
# SessionLocal est probablement un `sessionmaker` de SQLAlchemy/SQLModel pour créer des sessions de BDD.
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
    # Utilise un contexte `with` pour s'assurer que la session de base de données est toujours fermée, même en cas d'erreur.
    with SessionLocal() as sess:

        # BLOC 1 : VÉRIFICATIONS DE SÉCURITÉ ET D'ACCÈS
        # 1. On vérifie d'abord que l'équipe demandée existe bien en base de données.
        team = sess.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Équipe non trouvée")

        # 2. On s'assure que l'utilisateur authentifié est un membre actif de cette équipe
        #    (c'est-à-dire que son invitation a été acceptée : `accepted_at` n'est pas nul).
        if not any(m.user_id == current_user.id and m.accepted_at for m in team.members):
            raise HTTPException(403, "Accès interdit : pas membre de l'équipe")

        # BLOC 2 : CALCUL DU SCORE DE CONFORMITÉ (COMPLIANCE)
        # Cette section récupère tous les projets de l'équipe et calcule un score de conformité
        # basé sur les réponses à une checklist (probablement liée à une norme comme ISO 42001).
        projects: List[AIProject] = sess.exec(
            select(AIProject).where(AIProject.team_id == team_id)
        ).all()
        total_projects = len(projects)

        compliance_scores = []
        compliance_details = []

        # On boucle sur chaque projet pour calculer son score individuel.
        for p in projects:
            total_questions = 0
            compliant_questions = 0
            # On itère sur les "checklist_items" du projet, qui semblent contenir
            # les résultats (status) pour chaque point de contrôle.
            for item in p.checklist_items:
                statuses = item.results or []
                for status in statuses:
                    total_questions += 1
                    if status == "compliant":
                        compliant_questions += 1

            # Calcul du score en pourcentage pour le projet.
            score = round(float((compliant_questions / total_questions) * 100), 3) if total_questions > 0 else 0
            compliance_scores.append(score)

            # On stocke les détails pour chaque projet qui seront renvoyés dans la réponse.
            compliance_details.append({
                "project_id": p.id,
                "project_title": p.title,
                "description": p.description or "",
                "category": p.category or "Non défini",
                "owner": p.owner or "Inconnu",
                "createdAt": p.created_at.isoformat(),
                "status": p.status or "active",
                "riskLevel": "medium",  # Valeur par défaut
                "compliance_score": score,
                "total_questions": total_questions,
                "conform_questions": compliant_questions
            })

        # Calcul du score de conformité moyen pour toute l'équipe.
        average_compliance = round(sum(compliance_scores) / len(compliance_scores), 3) if compliance_scores else 0

        # BLOC 3 : AGRÉGATION DES INDICATEURS CLÉS (KPIs)
        # Comptage des non-conformités "majeures" qui ne sont pas encore corrigées.
        major_nc_count = sum(
            1 for p in projects
            for item in p.checklist_items
            for nc in item.non_conformites
            if nc.type_nc.lower() == "majeure" and nc.statut.lower() != "corrigee"
        )

        # Comptage des actions correctives qui sont encore ouvertes ou en cours.
        # La liste de statuts est large pour couvrir plusieurs langues/formats.
        open_actions_count = len(sess.exec(
            select(ActionCorrective)
            .where(ActionCorrective.status.in_([
                "to-do", "in-progress", "in-review",
                "non_corrigee", "non corrigée", "non corrigé", "non_corrigée",
                "ouverte", "en_cours", "en cours"
            ]))
        ).all())

        # BLOC 4 : RÉCUPÉRATION DES ACTIVITÉS RÉCENTES
        # On récupère la dernière évaluation pour chaque projet de l'équipe.
        evaluation_summaries = []
        for p in projects:
            last_eval = sess.exec(
                select(EvaluationRun)
                .where(EvaluationRun.project_id == p.id)
                .order_by(EvaluationRun.created_at.desc())
            ).first()

            if last_eval:
                evaluation_summaries.append({
                    "project_id": p.id, "project_title": p.title,
                    "evaluation_date": last_eval.created_at.isoformat(),
                    "status": last_eval.status, "metrics": last_eval.metrics,
                })
            else:
                evaluation_summaries.append({
                    "project_id": p.id, "project_title": p.title,
                    "evaluation_date": None, "status": "non évalué", "metrics": {}
                })

        # On récupère les 5 commentaires les plus récents postés sur n'importe
        # quel projet de l'équipe. La requête utilise une jointure et un tri.
        recent_comments = sess.exec(
            select(Comment)
            .join(AIProject, Comment.project_id == AIProject.id)
            .where(AIProject.team_id == team_id)
            .order_by(Comment.date.desc())
            .limit(5)
        ).all()

        recent_comments_list = [{
            "comment_id": c.id, "project_id": c.project_id,
            "author": c.author, "content": c.content, "date": c.date.isoformat(),
        } for c in recent_comments]

        # BLOC 5 : CONSTRUCTION DE LA RÉPONSE FINALE
        # Toutes les données collectées sont assemblées dans un unique dictionnaire
        # qui sera renvoyé au client front-end.
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