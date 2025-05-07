# app/models.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, LargeBinary
from sqlmodel import Field, SQLModel


# ─────────────── Users & Roles ───────────────
class Role(SQLModel, table=True):
    id:   Optional[int] = Field(default=None, primary_key=True)
    name: str


class User(SQLModel, table=True):
    id:            Optional[int] = Field(default=None, primary_key=True)
    username:      str           = Field(index=True, unique=True)
    password_hash: str
    role_id:       int           = Field(foreign_key="role.id")


# ─────────────── Documents ───────────────
class DocumentBase(SQLModel):
    title:   str
    content: str  # markdown


class Document(DocumentBase, table=True):
    id:         Optional[int] = Field(default=None, primary_key=True)
    version:    int           = Field(default=1)
    created_at: datetime      = Field(default_factory=datetime.utcnow)
    updated_at: datetime      = Field(default_factory=datetime.utcnow)
    created_by: str


# ─────────────── Document Images (BLOB) ───────────────
class DocumentImage(SQLModel, table=True):
    id:          Optional[int] = Field(default=None, primary_key=True)
    document_id: int           = Field(foreign_key="document.id", index=True)
    filename:    str
    mime_type:   str            = Field(default="image/png")
    data:        bytes          = Field(sa_column=Column(LargeBinary))


# ─────────────── DTOs sent over the API ───────────────
class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id:         int
    version:    int
    created_at: datetime
    updated_at: datetime
    created_by: str

    model_config = {"from_attributes": True}


class DocumentHistory(DocumentRead, table=True):
    id:          Optional[int] = Field(default=None, primary_key=True)
    document_id: int           = Field(foreign_key="document.id")
    changed_at:  datetime      = Field(default_factory=datetime.utcnow)

class UserRead(SQLModel):
    id:   int
    username: str

    class Config:
        orm_mode = True

# ─────────── AI Project Models ───────────
class AIProjectBase(SQLModel):
    name: str
    description: str
    status: str  # e.g. "draft", "active", "archived"
    objectives: Optional[str] = None
    stakeholders: Optional[str] = None


class AIProject(AIProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    risk_level: str = Field(default="unknown")  # placeholder initial


class AIProjectCreate(AIProjectBase):
    pass


class AIProjectRead(AIProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    risk_level: str

    model_config = {"from_attributes": True}