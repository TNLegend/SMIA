#app/models.py
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Column, LargeBinary, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.ext.mutable import MutableList
from sqlmodel import Field, SQLModel, Relationship


# ─────── USERS ───────

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role_id: int = Field(foreign_key="role.id")

# ─────── DOCUMENTS ───────

class DocumentBase(SQLModel):
    title: str
    content: str

class Document(DocumentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class DocumentImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    filename: str
    mime_type: str = Field(default="image/png")
    data: bytes = Field(sa_column=Column(LargeBinary))

class DocumentCreate(DocumentBase):
    pass

class DocumentRead(DocumentBase):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True

class DocumentHistory(DocumentRead, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    changed_at: datetime = Field(default_factory=datetime.utcnow)

class UserRead(SQLModel):
    id: int
    username: str

    class Config:
        from_attributes = True

# ─────── AI PROJECT MODELS ───────

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
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    author: str
    date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    content: str

    class Config:
        from_attributes = True

class CommentCreate(SQLModel):
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
    title: str
    description: str
    status: str
    objectives: Optional[str] = None
    stakeholders: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    compliance_score: int = 0
    progress: int = 0
    domain: Optional[str] = None

    tags: List[str] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    phases: List[Phase] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    team: List[TeamMember] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    risks: List[Risk] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    comments: List[Comment] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    ai_details: Optional[AIDetails] = Field(default=None, sa_column=Column(SQLiteJSON))

    class Config:
        alias_generator: Callable[[str], str] = to_camel
        from_attributes = True
        populate_by_name = True

class AIProject(AIProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checklist_items: List["ISO42001ChecklistItem"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",  # ← UNIQUEMENT ICI
            "single_parent": True  # ← requis avec delete-orphan
        },
    )
    model_runs: List["ModelRun"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )
    datasets: List["DataSet"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )
    evaluation_runs: List["EvaluationRun"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )
    artifacts: List["ModelArtifact"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )



class AIProjectCreate(AIProjectBase):
    pass

class AIProjectRead(AIProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ISO42001ChecklistItemBase(SQLModel):
    project_id: int
    control_id: str
    control_name: str
    description: str
    audit_questions: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(SQLiteJSON)
    )
    evidence_required: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(SQLiteJSON)
    )

class ISO42001ChecklistItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id")
    control_id: str
    control_name: str
    description: str
    audit_questions: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(SQLiteJSON)
    )
    evidence_required: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(SQLiteJSON)
    )
    statuses: List[str] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(SQLiteJSON))
    )
    results: List[str] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(SQLiteJSON))
    )
    observations: List[Optional[str]] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(SQLiteJSON))
    )
    actions_correctives: List["ActionCorrective"] = Relationship(
    back_populates = "checklist_item",
    sa_relationship_kwargs = {"cascade": "all, delete-orphan", "single_parent": True},
    )
    status: str
    result: str
    observation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    project: AIProject = Relationship(back_populates="checklist_items")
    proofs: List["Proof"] = Relationship(back_populates="checklist_item")


class Proof(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    checklist_item_id: int = Field(foreign_key="iso42001checklistitem.id")
    evidence_id: str = Field(index=True)              # <── NOUVEAU
    filename: str
    content: bytes = Field(sa_column=Column(LargeBinary))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    checklist_item: ISO42001ChecklistItem = Relationship(back_populates="proofs")

    __table_args__ = (
        UniqueConstraint(
            "checklist_item_id", "evidence_id", "filename",
            name="uq_item_evidence_file"
        ),
    )

class ISO42001ChecklistItemRead(SQLModel):
    id: int
    control_id: str
    control_name: str
    description: str
    audit_questions: List[Dict[str, Any]]
    evidence_required: List[Dict[str, Any]]
    status: str
    result: str
    observation: Optional[str]
    evidence_url: Optional[str] = Field(None, alias="evidence_url")

    class Config:
        from_attributes = True
        populate_by_name = True

class ActionCorrective(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    deadline: datetime
    status: str
    checklist_item_id: int = Field(foreign_key="iso42001checklistitem.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checklist_item: "ISO42001ChecklistItem" = Relationship(
    back_populates = "actions_correctives"
    )

#----------MODEL RUNS-------------

class ModelRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: str  # "pending"|"running"|"succeeded"|"failed"
    logs: Optional[str] = None
    project: AIProject = Relationship(back_populates="model_runs")
    artifacts: List["ModelArtifact"] = Relationship(
    back_populates = "run",
    sa_relationship_kwargs = {"cascade": "all, delete-orphan", "single_parent": True},
    )

class DataSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    kind: str                     # "train" | "test"
    path: str                     # chemin absolu sur disque
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    columns: List[str] = Field(sa_column=Column(SQLiteJSON))

    project: "AIProject" = Relationship(
        back_populates="datasets",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "single_parent": True
        }
    )
    config: Optional["DataConfig"] = Relationship(
        back_populates="dataset",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "single_parent": True,
            "uselist": False,
        }
    )



class DataConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # ondelete="CASCADE" pour que, au niveau SQL, la suppression du DataSet supprime aussi le DataConfig
    dataset_id: int = Field(
        sa_column=Column(
            ForeignKey("dataset.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    features: List[str] = Field(sa_column=Column(SQLiteJSON))
    target: str
    sensitive_attrs: List[str] = Field(sa_column=Column(SQLiteJSON))

    dataset: DataSet = Relationship(
        back_populates="config"
    )

class DataConfigCreate(BaseModel):
    dataset_id: int
    features: List[str] = Field(min_items=1)
    target: str
    sensitive_attrs: List[str] = Field(default_factory=list)


class EvaluationRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    model_run_id: int = Field(foreign_key="modelrun.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: str  # pending | running | succeeded | failed
    metrics: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLiteJSON))
    logs: Optional[str] = None

    project: "AIProject" = Relationship(back_populates="evaluation_runs")


class ModelArtifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    model_run_id: int = Field(foreign_key="modelrun.id")
    path: str  # chemin absolu
    format: str  # 'pt', 'joblib', 'onnx', …
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLiteJSON))

    project: "AIProject" = Relationship(back_populates="artifacts")
    run: "ModelRun" = Relationship(back_populates="artifacts")