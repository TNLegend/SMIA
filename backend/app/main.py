#app/main.py
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# Imports des modules de l'application
from app.db import init_db
from app.auth import router as auth_router
from app.routers.documents import router as docs_router
from app.routers.projects import router as projects_router
from app.routers import templates, artifacts, evaluations, dashboard
from app.routers.models import router as models_router
from app.routers.teams import router as teams_router
from app.routers.notifications import router as notification_router
from app.routers.report import router as report_router # Renommé pour éviter conflit de nom
# Imports des tâches planifiées
from app.tasks.cleanup import start_scheduler as cleanup_scheduler
from app.tasks.scheduler import start_scheduler as notif_scheduler

# ─── CONFIGURATION GLOBALE DU LOGGING ───────────────────────────────────
# BLOC DE CONFIGURATION DU LOGGING
# Cette configuration est appliquée à toute l'application. Elle définit un format
# standard pour tous les messages de log, incluant la date, le niveau de sévérité,
# et le nom du module, ce qui facilite grandement le débogage.
logging.basicConfig(
    level=logging.INFO, # Changé à INFO pour une verbosité raisonnable en production
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app")
logger.info("Starting SMIA API...")

# Constante pour la taille maximale des uploads
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MiB

# ─── INITIALISATION DE L'APPLICATION FASTAPI ──────────────────────────────
# BLOC D'INITIALISATION DE L'APPLICATION ET MIDDLEWARES
# Crée l'instance principale de FastAPI et configure ses middlewares.
app = FastAPI(
    title="SMIA API",
    description="Backend FastAPI pour la plateforme SMIA",
    version="0.1.0",
)

@app.middleware("http")
async def limit_content_length(request: Request, call_next):
    """
    Middleware personnalisé pour rejeter les requêtes trop volumineuses
    avant même qu'elles n'atteignent la logique des routes. C'est une mesure
    de sécurité et de performance importante pour prévenir les attaques par déni de service.
    """
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_UPLOAD_SIZE:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    return await call_next(request)

# Ajout du middleware CORS (Cross-Origin Resource Sharing)
# C'est une configuration de sécurité indispensable pour permettre à une application
# web front-end (ex: tournant sur localhost:3000) de communiquer avec cette API.
app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "http://localhost:5173"], # Autorise le front-end local
  allow_methods=["*"], # Autorise toutes les méthodes HTTP (GET, POST, etc.)
  allow_headers=["*"], # Autorise tous les en-têtes
  allow_credentials=True, # Autorise l'envoi de cookies (pour l'authentification)
)

# ─── ÉVÉNEMENTS DE DÉMARRAGE ─────────────────────────────────────────────
# BLOC DE GESTION DES TÂCHES AU DÉMARRAGE
# La fonction décorée avec `@app.on_event("startup")` est exécutée une seule
# fois, au moment où le serveur FastAPI démarre.
@app.on_event("startup")
def on_startup():
    """Initialise la base de données et lance les tâches planifiées."""
    init_db() # Crée les tables de la BDD si elles n'existent pas.
    cleanup_scheduler() # Démarre le planificateur pour les tâches de nettoyage.
    notif_scheduler() # Démarre le planificateur pour les notifications.
    logger.info("Database initialized and schedulers started.")


# ─── INCLUSION DES ROUTEURS ─────────────────────────────────────────────
# BLOC D'ASSEMBLAGE DES ROUTEURS
# C'est ici que tous les modules d'API que nous avons documentés sont "branchés"
# sur l'application principale. Chaque `include_router` ajoute un ensemble de
# routes (endpoints) à l'API, en respectant le préfixe défini dans chaque fichier.
app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(projects_router)
app.include_router(models_router)
app.include_router(evaluations.router)
app.include_router(docs_router)
app.include_router(templates.router)
app.include_router(artifacts.router)
app.include_router(notification_router)
app.include_router(report_router)
app.include_router(dashboard.router)