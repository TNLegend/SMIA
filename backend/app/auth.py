# Authentication routes and helpers
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
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, constr
from sqlmodel import Session, select, delete

from app.db import SessionLocal
from app.models import (
    User,
    UserRead,  # your Pydantic “public” DTO
    ISO42001ChecklistItem,
    Proof,
    AIProject,
    Document,
    DocumentHistory,
    DocumentImage, TeamMembership, Team,
)
from app.utils.files import purge_project_storage

# ─── JWT CONFIG ───────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "siwarbellalah")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    with SessionLocal() as sess:
        yield sess


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


# ─── PAYLOAD SCHEMAS ───────────────────────────────────────
class UpdateUser(BaseModel):
    username: Optional[constr(strip_whitespace=True, min_length=1)] = None
    password: Optional[constr(min_length=8)] = None


# ─── SIGNUP & LOGIN ────────────────────────────────────────
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    existing = db.exec(select(User).where(User.username == form_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=form_data.username,
        password_hash=hash_password(form_data.password),
        role_id=1,
    )
    db.add(user)
    db.commit()
    return {"msg": "User created"}


@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
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
        httponly=True,
        samesite="lax",
    )
    return {"access_token": token, "token_type": "bearer"}


# ─── CURRENT USER DEPENDENCY ──────────────────────────────
def get_current_user(
    header_token: str | None = Depends(oauth2_scheme),
    cookie_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    token = header_token or cookie_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ─── USER‐SELF ENDPOINTS ──────────────────────────────────
@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserRead)
def update_me(
    payload: UpdateUser,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = False

    if payload.username and payload.username != current_user.username:
        # Optionally enforce uniqueness:
        if db.exec(select(User).where(User.username == payload.username)).first():
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = payload.username
        updated = True

    if payload.password:
        current_user.password_hash = hash_password(payload.password)
        updated = True

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes detected."
        )

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 0) Drop memberships and owned teams explicitly
    db.exec(delete(TeamMembership).where(TeamMembership.user_id == current_user.id))

    owned_teams = db.exec(select(Team).where(Team.owner_id == current_user.id)).all()
    for team in owned_teams:
        db.delete(team)
    # 1) delete all AIProjects and nested data
    projects = db.exec(select(AIProject).where(AIProject.owner == current_user.username)).all()
    for proj in projects:
        # delete checklist proofs
        item_ids = db.exec(
            select(ISO42001ChecklistItem.id).where(ISO42001ChecklistItem.project_id == proj.id)
        ).all()
        if item_ids:
            db.exec(delete(Proof).where(Proof.checklist_item_id.in_(item_ids)))
        # purge disk
        purge_project_storage(proj.id)
        db.delete(proj)

    # 2) delete all Documents + history + images
    docs = db.exec(select(Document).where(Document.created_by == current_user.username)).all()
    for doc in docs:
        db.exec(delete(DocumentHistory).where(DocumentHistory.document_id == doc.id))
        db.exec(delete(DocumentImage).where(DocumentImage.document_id == doc.id))
        db.delete(doc)

    # 3) finally delete the user
    db.delete(current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
