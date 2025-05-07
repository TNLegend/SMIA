# app/models.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any, Callable

from sqlalchemy import Column, LargeBinary, JSON, String
from sqlmodel import Field, SQLModel
from pydantic import root_validator



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
def to_camel(string: str) -> str:
    parts = string.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])

class Phase(SQLModel):
    name: str
    status: str
    date: str

class TeamMember(SQLModel):
    name: str
    role: str
    avatar: str

class Risk(SQLModel):
    category: str
    description: str
    level: str
    impact: int
    probability: int
    status: str
    date: str
    mitigation: Optional[str] = None

class Comment(SQLModel):
    author: str
    date: str
    content: str

class AIDetails(SQLModel):
    type: str
    model: str
    framework: str
    dataset_size: str
    features_count: int
    accuracy: int
    training_time: str

class AIProjectBase(SQLModel):
    name: str
    description: str
    status: str  # e.g. "draft", "active", "completed", "on-hold"
    objectives: Optional[str] = None
    stakeholders: Optional[str] = None

    # ⬇ new fields driven by your front end:
    category: Optional[str] = None
    owner: Optional[str] = None
    compliance_score: int = 0
    progress: int = 0
    domain: Optional[str] = None

    tags:       List[str]       = Field(default_factory=list, sa_column=Column(JSON))
    phases:     List[Phase]     = Field(default_factory=list, sa_column=Column(JSON))
    team:       List[TeamMember]= Field(default_factory=list, sa_column=Column(JSON))
    risks:      List[Risk]      = Field(default_factory=list, sa_column=Column(JSON))
    comments:   List[Comment]   = Field(default_factory=list, sa_column=Column(JSON))
    ai_details: Optional[AIDetails]= Field(default=None, sa_column=Column(JSON))

    class Config:
        alias_generator: Callable[[str], str] = to_camel
        allow_population_by_field_name = True
        populate_by_name = True

class AIProject(AIProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AIProjectCreate(AIProjectBase):
    pass

class AIProjectRead(AIProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config(AIProjectBase.Config):
        orm_mode = True