from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.auth import router as auth_router
from app.routers.documents import router as docs_router
from app.routers.projects import router as projects_router

app = FastAPI(
    title="SMIA API",
    description="Backend FastAPI pour la plateforme SMIA",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],       # nécessaire pour Authorization
    allow_credentials=True,    # pour que le cookie smia_token soit envoyé
    expose_headers=["Content-Disposition"],
)

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(projects_router)