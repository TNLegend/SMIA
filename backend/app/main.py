#app/main.py
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.auth import router as auth_router
from app.routers.documents import router as docs_router
from app.routers.projects import router as projects_router
from app.routers import templates, artifacts
from app.routers.models import router as models_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.tasks.cleanup import start_scheduler


# ——— Configuration du logging global ———
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app")
logger.debug("Starting SMIA API...")

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MiB

app = FastAPI(
    title="SMIA API",
    description="Backend FastAPI pour la plateforme SMIA",
    version="0.1.0",
)
@app.middleware("http")
async def limit_content_length(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_UPLOAD_SIZE:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    return await call_next(request)

@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()
    logger.debug("Database initialized")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],  # ou ["*"] en dev
  allow_methods=["*"],
  allow_headers=["*"],
  allow_credentials=True,
)

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(projects_router)
app.include_router(models_router)
app.include_router(templates.router)
app.include_router(artifacts.router)

