#app/models.py
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Column, LargeBinary, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.ext.mutable import MutableList
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum
from datetime import date
# ─────── USERS ───────

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)

    # relation inverse (optionnelle)
    users: List["User"] = Relationship(back_populates="role")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password_hash: str

    role_id: Optional[int] = Field(foreign_key="role.id", default=None)
    role: Optional[Role] = Relationship(back_populates="users")

    # équipes qu’il possède
    owned_teams: List["Team"] = Relationship(back_populates="owner")
    # adhésions aux équipes
    teams: List["TeamMembership"] = Relationship(back_populates="user")

class TeamMemberResponse(BaseModel):
    name: str
    role: str
    avatar: Optional[str] = None  # avatar optionnel, peut être une URL

    class Config:
        orm_mode = True

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    owner_id: int = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # qui possède l’équipe
    owner: User = Relationship(back_populates="owned_teams")
    # tous ses membres
    members: List["TeamMembership"] = Relationship(
            back_populates = "team",
            sa_relationship_kwargs = {
                    "cascade": "all, delete-orphan",
                    "single_parent": True,
        },
    )
    projects: List["AIProject"] = Relationship(
            back_populates = "team",
            sa_relationship_kwargs = {
                    "cascade": "all, delete-orphan",
                    "single_parent": True,
        },
        )
    documents: List["Document"] = Relationship(
            back_populates = "team",
            sa_relationship_kwargs = {
                    "cascade": "all, delete-orphan",
                    "single_parent": True,
        },
    )


class TeamMembership(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "team_id", name="uq_user_team"),
    )

    user_id: int = Field(foreign_key="user.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    role: str = Field(
        default="member",
        description="owner | manager | member",
        nullable=False
    )
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    user: User = Relationship(back_populates="teams")
    team: Team = Relationship(back_populates="members")

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
    team_id: int = Field(foreign_key="team.id", nullable=False, index=True)
    team: "Team" = Relationship(back_populates="documents")

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

class Comment(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", nullable=False, index=True)
    author: str
    content: str
    date: datetime = Field(default_factory=datetime.utcnow)

    project: "AIProject" = Relationship(back_populates="comments")

class CommentCreate(SQLModel):
    content: str

class AIDetails(SQLModel):
    type: str
    model: str
    framework: str
    dataset_size: int
    features_count: int
    accuracy: float
    r2: float
    training_time: float

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        populate_by_name = True


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
    team_members: List[TeamMember] = Field(
    default_factory = list,
    sa_column = Column(SQLiteJSON),
    description = "(JSON) metadata about your team members"
    )
    risks: List[Risk] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    ai_details: Optional[AIDetails] = Field(default=None, sa_column=Column(SQLiteJSON))

    class Config:
        alias_generator: Callable[[str], str] = to_camel
        from_attributes = True
        populate_by_name = True

class AIProject(AIProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    team_id: int = Field(foreign_key="team.id", nullable=False, index=True)
    team: "Team" = Relationship(back_populates="projects")
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
    comments: List[Comment] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    notifications: List["Notification"] = Relationship(back_populates="project",
                                                       sa_relationship_kwargs={"cascade": "all, delete-orphan"})



class AIProjectCreate(AIProjectBase):
    class Config:
        orm_mode = True

class AIProjectRead(AIProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    team_id: int
    team_members: List[TeamMemberResponse] = []

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
class TypeNonConformite(str, Enum):
    mineure = "mineure"
    majeure = "majeure"

class StatutNonConformite(str, Enum):
    non_corrigee = "non_corrigee"
    en_cours     = "en_cours"
    corrigee     = "corrigee"
    ferme        = "ferme"

class NonConformiteBase(BaseModel):
    type_nc: TypeNonConformite
    deadline_correction: Optional[datetime] = None
    statut: StatutNonConformite = StatutNonConformite.non_corrigee

class NonConformiteCreate(NonConformiteBase):
    pass

class NonConformiteUpdate(BaseModel):
    type_nc: Optional[TypeNonConformite] = None
    deadline_correction: Optional[datetime] = None
    statut: Optional[StatutNonConformite] = None

class NonConformiteRead(BaseModel):
    id: int
    checklist_item_id: int
    question_index: int
    type_nc: str  # mineure / majeure
    deadline_correction: Optional[datetime]
    statut: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class NonConformite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    checklist_item_id: int = Field(foreign_key="iso42001checklistitem.id", nullable=False, index=True)
    question_index: int = Field(nullable=False, index=True)  # <-- Nouveau champ

    type_nc: TypeNonConformite = Field(nullable=False)
    deadline_correction: Optional[datetime] = None
    statut: StatutNonConformite = Field(default=StatutNonConformite.non_corrigee)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    checklist_item: "ISO42001ChecklistItem" = Relationship(back_populates="non_conformites")

    actions_correctives: List["ActionCorrective"] = Relationship(
        back_populates="non_conformite",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
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
    non_conformites: List[NonConformite] = Relationship(
        back_populates="checklist_item",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )


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

    checklist_item_id: int = Field(foreign_key="iso42001checklistitem.id", nullable=True)
    non_conformite_id: int = Field(foreign_key="nonconformite.id", nullable=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    checklist_item: Optional["ISO42001ChecklistItem"] = Relationship(back_populates="actions_correctives")
    non_conformite: Optional[NonConformite] = Relationship(back_populates="actions_correctives")
    responsible_user_id: Optional[int] = Field(default=None, foreign_key="user.id", nullable=True)
    responsible_user: Optional[User] = Relationship()


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id", nullable=False, index=True)
    project_id: int = Field(foreign_key="aiproject.id", nullable=False, index=True)
    nonconformite_id: Optional[int] = Field(foreign_key="nonconformite.id", nullable=True, index=True)
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = Field(default=False)

    # Relations optionnelles
    project: Optional["AIProject"] = Relationship(back_populates="notifications")
    non_conformite: Optional["NonConformite"] = Relationship()

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
    train_config: Optional["DataConfig"] = Relationship(
        back_populates="train_dataset",
        sa_relationship_kwargs={
            "foreign_keys": "[DataConfig.train_dataset_id]",
            "cascade": "all, delete-orphan",
            "single_parent": True,
            "uselist": False,
        },
    )

    test_config: Optional["DataConfig"] = Relationship(
        back_populates="test_dataset",
        sa_relationship_kwargs={
            "foreign_keys": "[DataConfig.test_dataset_id]",
            "cascade": "all, delete-orphan",
            "single_parent": True,
            "uselist": False,
        },
    )



class DataConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # ondelete="CASCADE" pour que, au niveau SQL, la suppression du DataSet supprime aussi le DataConfig
    train_dataset_id: int = Field(
        sa_column=Column(ForeignKey("dataset.id", ondelete="CASCADE")),
        description="The ID of the training DataSet",
    )
    test_dataset_id: int = Field(
        sa_column=Column(ForeignKey("dataset.id", ondelete="CASCADE")),
        description="The ID of the testing DataSet",
    )
    features: List[str] = Field(sa_column=Column(SQLiteJSON))
    target: Optional[str] = Field(default=None, nullable=True)
    sensitive_attrs: List[str] = Field(sa_column=Column(SQLiteJSON))

    train_dataset: DataSet = Relationship(
        back_populates="train_config",
        sa_relationship_kwargs={
            "foreign_keys": "[DataConfig.train_dataset_id]",
        },
    )

    test_dataset: DataSet = Relationship(
        back_populates="test_config",
        sa_relationship_kwargs={
            "foreign_keys": "[DataConfig.test_dataset_id]",
        },
    )

class DataConfigCreate(BaseModel):
    train_dataset_id: int
    test_dataset_id: int
    features: List[str] = Field(min_items=1)
    target:           Optional[str] = None
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