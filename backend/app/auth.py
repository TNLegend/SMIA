import os
from datetime import datetime, timedelta

from fastapi import (
    APIRouter, Depends, HTTPException, status, Response, Cookie
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.db import SessionLocal
from app.models import User
from app.models import UserRead  # you'll need a DTO


# ─── Configuration JWT ──────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "siwarbellalah")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Helpers ────────────────────────────────────────────────────────────────
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


# ─── Signup & Login ────────────────────────────────────────────────────────
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    existing = db.exec(select(User).where(User.username == form_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=form_data.username,
        password_hash=hash_password(form_data.password),
        role_id=1  # rôle par défaut
    )
    db.add(user)
    db.commit()
    return {"msg": "User created"}


@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(str(user.id))
    # on renvoie aussi un cookie HTTP-Only
    response.set_cookie(
        key="smia_token",
        value=token,
        httponly=True,
        samesite="lax",  # en prod : "strict" ou "none; secure"
    )
    return {"access_token": token, "token_type": "bearer"}


# ─── Dépendance current_user ───────────────────────────────────────────────
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

@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    # get_current_user already verified signature & exp
    return current_user
