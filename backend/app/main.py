import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.auth import router as auth_router
from app.routers.documents import router as docs_router
from app.routers.projects import router as projects_router
from fastapi.staticfiles import StaticFiles
# ——— Configuration du logging global ———
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app")
logger.debug("Starting SMIA API...")

app = FastAPI(
    title="SMIA API",
    description="Backend FastAPI pour la plateforme SMIA",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup():
    init_db()
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
