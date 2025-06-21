import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    Cookie,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# Passlib est utilisé pour le hachage et la vérification sécurisés des mots de passe.
from passlib.context import CryptContext
# python-jose est utilisé pour la création et la validation des JSON Web Tokens (JWT).
from jose import JWTError, jwt
from pydantic import BaseModel, constr
from sqlmodel import Session, select, delete

from app.db import SessionLocal
from app.models import (
    User,
    UserRead,
    ISO42001ChecklistItem,
    Proof,
    AIProject,
    Document,
    DocumentHistory,
    DocumentImage, TeamMembership, Team,
)
from app.utils.files import purge_project_storage

# ─── CONFIGURATION JWT ET SÉCURITÉ ───────────────────────────────────────────
# BLOC DE CONFIGURATION
# Cette section initialise les paramètres pour la gestion des tokens et des mots de passe.
# Les valeurs sont chargées depuis les variables d'environnement pour plus de flexibilité et de sécurité.

JWT_SECRET = os.getenv("JWT_SECRET",
                       "siwarbellalah")  # Clé secrète pour signer les tokens. À CHANGER pour la production.
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # Algorithme de signature.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))  # Durée de validité du token.

# Contexte pour le hachage des mots de passe utilisant l'algorithme bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Schéma de sécurité OAuth2 standard de FastAPI pour la gestion des tokens.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── FONCTIONS UTILITAIRES (HELPERS) ───────────────────────────────────────
# BLOC DES FONCTIONS D'AIDE
# Fonctions réutilisées pour la gestion de la BDD, des mots de passe et des tokens.

def get_db():
    """Dépendance FastAPI pour fournir une session de base de données par requête."""
    with SessionLocal() as sess:
        yield sess


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond à sa version hachée."""
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    """Hache un mot de passe en utilisant bcrypt."""
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    """Crée un nouveau JSON Web Token (JWT) pour un sujet donné (ici, l'ID de l'utilisateur)."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}  # Le "payload" du token
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


# ─── SCHÉMAS DE DONNÉES (PAYLOADS) ───────────────────────────────────────
class UpdateUser(BaseModel):
    """Schéma Pydantic pour la mise à jour des informations utilisateur."""
    username: Optional[constr(strip_whitespace=True, min_length=1)] = None
    password: Optional[constr(min_length=8)] = None


# ─── INSCRIPTION ET CONNEXION (SIGNUP & LOGIN) ──────────────────────────────────
# BLOC DE GESTION DE L'INSCRIPTION ET DE LA CONNEXION
# Ces routes constituent le point d'entrée pour les utilisateurs dans l'application.

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
        form_data: OAuth2PasswordRequestForm = Depends(),  # Utilise le format standard pour les formulaires de login.
        db: Session = Depends(get_db),
):
    # Route pour créer un nouveau compte utilisateur.
    # 1. Vérifie si le nom d'utilisateur existe déjà pour éviter les doublons.
    # 2. Hache le mot de passe fourni avant de le stocker.
    # 3. Crée et sauvegarde le nouvel utilisateur en base de données.
    existing = db.exec(select(User).where(User.username == form_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(
        username=form_data.username,
        password_hash=hash_password(form_data.password),
        role_id=1,  # `role_id=1` est probablement le rôle par défaut.
    )
    db.add(user)
    db.commit()
    return {"msg": "User created"}


@router.post("/login")
def login(
        response: Response,  # La réponse FastAPI est injectée pour pouvoir y ajouter un cookie.
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
):
    # Route pour connecter un utilisateur et lui fournir un token d'accès.
    # 1. Récupère l'utilisateur par son nom d'utilisateur.
    # 2. Vérifie que l'utilisateur existe et que le mot de passe est correct.
    # 3. Si les identifiants sont valides, crée un token JWT.
    # 4. PRATIQUE DE SÉCURITÉ : Place le token dans un cookie `HttpOnly`. Cela empêche
    #    l'accès au token via JavaScript côté client, protégeant contre les attaques XSS.
    # 5. Retourne également le token dans le corps de la réponse pour les clients
    #    qui ne gèrent pas les cookies (ex: applications mobiles).
    user = db.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(str(user.id))

    response.set_cookie(
        key="smia_token",
        value=token,
        httponly=True,  # Important pour la sécurité
        samesite="lax",
    )

    return {"access_token": token, "token_type": "bearer"}


# ─── DÉPENDANCE POUR OBTENIR L'UTILISATEUR COURANT ──────────────────────────────
# BLOC DE LA DÉPENDANCE D'AUTHENTIFICATION
# La fonction `get_current_user` est le pilier de la sécurité de l'API. Injectée
# dans la plupart des autres routes, elle est responsable de valider le token
# et de récupérer l'utilisateur correspondant en base de données.
def get_current_user(
        # Tente de récupérer le token depuis l'en-tête "Authorization: Bearer <token>"
        header_token: str | None = Depends(oauth2_scheme),
        # Si non trouvé, tente de le récupérer depuis un cookie nommé "smia_token"
        cookie_token: str | None = Cookie(None),
        db: Session = Depends(get_db),
):
    # 1. Stratégie de récupération du token flexible (Header ou Cookie).
    token = header_token or cookie_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # 2. Décodage et validation du JWT.
        #    `jwt.decode` vérifie automatiquement la signature et la date d'expiration.
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        # 3. Extraction de l'ID de l'utilisateur depuis le "subject" (`sub`) du token.
        user_id: str = payload.get("sub")
        if not user_id:
            raise JWTError()
    except JWTError:
        # Cette erreur est levée si le token est malformé, expiré ou si la signature est invalide.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 4. Récupération de l'utilisateur en base de données.
    user = db.get(User, int(user_id))
    if not user:
        # Ce cas peut arriver si l'utilisateur a été supprimé après l'émission du token.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 5. Retourne l'objet User complet, qui sera disponible dans la route qui utilise cette dépendance.
    return user


# ─── ENDPOINTS DE GESTION DU COMPTE UTILISATEUR (`/me`) ──────────────────────────────────
# BLOC DE GESTION DU COMPTE DE L'UTILISATEUR ("MON COMPTE")
# Cette section fournit les routes permettant à un utilisateur authentifié de gérer son propre profil.

@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    """Route simple pour récupérer les informations de son propre profil."""
    return current_user


@router.put("/me", response_model=UserRead)
def update_me(
        payload: UpdateUser,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    # Route pour mettre à jour son nom d'utilisateur ou son mot de passe.
    updated = False
    if payload.username and payload.username != current_user.username:
        if db.exec(select(User).where(User.username == payload.username)).first():
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = payload.username
        updated = True
    if payload.password:
        current_user.password_hash = hash_password(payload.password)
        updated = True
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes detected.")
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    # Route destructive pour permettre à un utilisateur de supprimer son propre compte
    # et toutes les données qui lui sont associées.
    # La logique effectue une suppression en cascade manuelle et explicite pour garantir
    # que toutes les données (en base et sur disque) sont bien nettoyées.

    # 0. Supprime les appartenances aux équipes et les équipes dont l'utilisateur est propriétaire.
    db.exec(delete(TeamMembership).where(TeamMembership.user_id == current_user.id))
    owned_teams = db.exec(select(Team).where(Team.owner_id == current_user.id)).all()
    for team in owned_teams:
        db.delete(team)

    # 1. Supprime tous les projets d'IA et leurs données associées.
    projects = db.exec(select(AIProject).where(AIProject.owner == current_user.username)).all()
    for proj in projects:
        item_ids = db.exec(select(ISO42001ChecklistItem.id).where(ISO42001ChecklistItem.project_id == proj.id)).all()
        if item_ids:
            db.exec(delete(Proof).where(Proof.checklist_item_id.in_(item_ids)))
        # Nettoyage des fichiers sur le disque dur.
        purge_project_storage(proj.id)
        db.delete(proj)

    # 2. Supprime tous les documents, leur historique et leurs images.
    docs = db.exec(select(Document).where(Document.created_by == current_user.username)).all()
    for doc in docs:
        db.exec(delete(DocumentHistory).where(DocumentHistory.document_id == doc.id))
        db.exec(delete(DocumentImage).where(DocumentImage.document_id == doc.id))
        db.delete(doc)

    # 3. Finalement, supprime l'utilisateur lui-même.
    db.delete(current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)