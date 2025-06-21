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

# ─────── GESTION DES UTILISATEURS, ÉQUIPES ET APPARTENANCES ───────
# BLOC DE MODÈLES - UTILISATEURS ET ÉQUIPES
# Définit les tables pour les utilisateurs (User), les rôles (Role), les équipes (Team)
# et la table de liaison pour leur appartenance (TeamMembership).

class Role(SQLModel, table=True):
    """Table des rôles (ex: admin, member)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    users: List["User"] = Relationship(back_populates="role")

class User(SQLModel, table=True):
    """Table des utilisateurs."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password_hash: str
    role_id: Optional[int] = Field(foreign_key="role.id", default=None)
    role: Optional[Role] = Relationship(back_populates="users")
    owned_teams: List["Team"] = Relationship(back_populates="owner")
    teams: List["TeamMembership"] = Relationship(back_populates="user")

class TeamMemberResponse(BaseModel):
    """DTO pour formater les membres d'une équipe dans les réponses API."""
    name: str; role: str; avatar: Optional[str] = None
    class Config: orm_mode = True

class Team(SQLModel, table=True):
    """Table des équipes."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    owner_id: int = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner: User = Relationship(back_populates="owned_teams")
    # `cascade="all, delete-orphan"` assure que la suppression d'une équipe
    # supprime automatiquement toutes ses appartenances, projets et documents.
    members: List["TeamMembership"] = Relationship(back_populates="team", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    projects: List["AIProject"] = Relationship(back_populates="team", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    documents: List["Document"] = Relationship(back_populates="team", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})

class TeamMembership(SQLModel, table=True):
    """Table de liaison pour l'appartenance d'un utilisateur à une équipe."""
    __table_args__ = (UniqueConstraint("user_id", "team_id", name="uq_user_team"),)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    role: str = Field(default="member", description="owner | manager | member", nullable=False)
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    user: User = Relationship(back_populates="teams")
    team: Team = Relationship(back_populates="members")

# ─────── GESTION DES DOCUMENTS ───────
# BLOC DE MODÈLES - DOCUMENTS
# Définit les tables pour les documents, leurs images, leur historique,
# et les DTOs associés pour les opérations CRUD.

class DocumentBase(SQLModel): title: str; content: str
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
    filename: str; mime_type: str = Field(default="image/png")
    data: bytes = Field(sa_column=Column(LargeBinary)) # Stockage binaire
class DocumentCreate(DocumentBase): pass
class DocumentRead(DocumentBase):
    id: int; version: int; created_at: datetime; updated_at: datetime; created_by: str
    class Config: from_attributes = True
class DocumentHistory(DocumentRead, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    changed_at: datetime = Field(default_factory=datetime.utcnow)

# ─────── SCHÉMAS DE LECTURE (DTOs) PUBLICS ───────
class UserRead(SQLModel):
    """DTO pour exposer les infos d'un utilisateur sans le hash du mot de passe."""
    id: int; username: str
    class Config: from_attributes = True

# ─────── MODÈLES POUR LES PROJETS D'IA ET LEURS COMPOSANTS ───────
# BLOC DE MODÈLES - PROJETS D'IA
# Section la plus complexe, définissant un projet d'IA et tous ses sous-composants :
# détails, risques, commentaires, checklist de conformité, actions, preuves, runs, etc.

def to_camel(s: str) -> str: return s.split('_')[0] + ''.join(w.capitalize() for w in s.split('_')[1:])
class Phase(SQLModel): name: str; status: str; date: str
class TeamMember(SQLModel): name: str; role: str; avatar: str
class Risk(SQLModel): category: str; description: str; level: str; impact: int; probability: int; status: str; date: str; mitigation: Optional[str] = None
class Comment(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", nullable=False, index=True)
    author: str; content: str; date: datetime = Field(default_factory=datetime.utcnow)
    project: "AIProject" = Relationship(back_populates="comments")
class CommentCreate(SQLModel): content: str
class AIDetails(SQLModel):
    type: str; model: str; framework: str; dataset_size: int; features_count: int; accuracy: float; r2: float; training_time: float
    class Config: alias_generator = to_camel; allow_population_by_field_name = True; populate_by_name = True

class AIProjectBase(SQLModel):
    """Champs de base pour un projet d'IA. Plusieurs champs complexes (listes d'objets)
    sont stockés sous forme de colonnes JSON en base de données."""
    title: str; description: str; status: str; objectives: Optional[str] = None; stakeholders: Optional[str] = None
    category: Optional[str] = None; owner: Optional[str] = None; compliance_score: int = 0; progress: int = 0; domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    phases: List[Phase] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    team_members: List[TeamMember] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    risks: List[Risk] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    ai_details: Optional[AIDetails] = Field(default=None, sa_column=Column(SQLiteJSON))
    class Config: alias_generator: Callable[[str], str] = to_camel; from_attributes = True; populate_by_name = True

class AIProject(AIProjectBase, table=True):
    """Table principale des projets d'IA, héritant de AIProjectBase et ajoutant les relations
    avec toutes les autres tables (checklist, runs, datasets, etc.). La suppression en
    cascade est activée pour toutes les relations, assurant un nettoyage complet."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow); updated_at: datetime = Field(default_factory=datetime.utcnow)
    team_id: int = Field(foreign_key="team.id", nullable=False, index=True)
    team: "Team" = Relationship(back_populates="projects")
    checklist_items: List["ISO42001ChecklistItem"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    model_runs: List["ModelRun"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    datasets: List["DataSet"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    evaluation_runs: List["EvaluationRun"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    artifacts: List["ModelArtifact"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    comments: List[Comment] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    notifications: List["Notification"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class AIProjectCreate(AIProjectBase): pass
class AIProjectRead(AIProjectBase):
    id: int; created_at: datetime; updated_at: datetime; team_id: int
    team_members: List[TeamMemberResponse] = [] # Ce champ est peuplé manuellement dans les routes

# --- Modèles de Conformité (ISO 42001) ---
class TypeNonConformite(str, Enum): mineure="mineure"; majeure="majeure"
class StatutNonConformite(str, Enum): non_corrigee="non_corrigee"; en_cours="en_cours"; corrigee="corrigee"; ferme="ferme"
class NonConformite(SQLModel, table=True):
    """Table des non-conformités, liées à une question précise d'un item de checklist."""
    id: Optional[int] = Field(default=None, primary_key=True)
    checklist_item_id: int = Field(foreign_key="iso42001checklistitem.id", nullable=False, index=True)
    question_index: int = Field(nullable=False, index=True)
    type_nc: TypeNonConformite = Field(nullable=False)
    deadline_correction: Optional[datetime] = None
    statut: StatutNonConformite = Field(default=StatutNonConformite.non_corrigee)
    created_at: datetime = Field(default_factory=datetime.utcnow); updated_at: datetime = Field(default_factory=datetime.utcnow)
    checklist_item: "ISO42001ChecklistItem" = Relationship(back_populates="non_conformites")
    actions_correctives: List["ActionCorrective"] = Relationship(back_populates="non_conformite", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
# ... (DTOs pour NonConformite)
class NonConformiteBase(BaseModel): type_nc: TypeNonConformite; deadline_correction: Optional[datetime]=None; statut: StatutNonConformite = StatutNonConformite.non_corrigee
class NonConformiteCreate(NonConformiteBase): pass
class NonConformiteUpdate(BaseModel): type_nc: Optional[TypeNonConformite]=None; deadline_correction:Optional[datetime]=None; statut:Optional[StatutNonConformite]=None
class NonConformiteRead(BaseModel):
    id:int; checklist_item_id:int; question_index:int; type_nc:str; deadline_correction:Optional[datetime]; statut:str; created_at:datetime; updated_at:datetime
    class Config: orm_mode=True

class ISO42001ChecklistItem(SQLModel, table=True):
    """Table des items de la checklist de conformité, un par point de contrôle de la norme."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id")
    control_id: str; control_name: str; description: str
    audit_questions: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    evidence_required: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(SQLiteJSON))
    statuses: List[str] = Field(default_factory=list, sa_column=Column(MutableList.as_mutable(SQLiteJSON)))
    results: List[str] = Field(default_factory=list, sa_column=Column(MutableList.as_mutable(SQLiteJSON)))
    observations: List[Optional[str]] = Field(default_factory=list, sa_column=Column(MutableList.as_mutable(SQLiteJSON)))
    status: str; result: str; observation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow); updated_at: datetime = Field(default_factory=datetime.utcnow)
    project: AIProject = Relationship(back_populates="checklist_items")
    proofs: List["Proof"] = Relationship(back_populates="checklist_item")
    actions_correctives: List["ActionCorrective"] = Relationship(back_populates="checklist_item", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    non_conformites: List[NonConformite] = Relationship(back_populates="checklist_item", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})

class Proof(SQLModel, table=True):
    """Table des preuves (fichiers) uploadées pour un item de checklist."""
    __table_args__ = (UniqueConstraint("checklist_item_id", "evidence_id", "filename", name="uq_item_evidence_file"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    checklist_item_id: int = Field(foreign_key="iso42001checklistitem.id")
    evidence_id: str = Field(index=True)
    filename: str
    content: bytes = Field(sa_column=Column(LargeBinary))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    checklist_item: ISO42001ChecklistItem = Relationship(back_populates="proofs")

class ActionCorrective(SQLModel, table=True):
    """Table des actions correctives, liées soit à un item de checklist, soit directement à une non-conformité."""
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str; deadline: datetime; status: str
    checklist_item_id: int = Field(foreign_key="iso42001checklistitem.id", nullable=True)
    non_conformite_id: int = Field(foreign_key="nonconformite.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow); updated_at: datetime = Field(default_factory=datetime.utcnow)
    checklist_item: Optional["ISO42001ChecklistItem"] = Relationship(back_populates="actions_correctives")
    non_conformite: Optional[NonConformite] = Relationship(back_populates="actions_correctives")
    responsible_user_id: Optional[int] = Field(default=None, foreign_key="user.id", nullable=True)
    responsible_user: Optional[User] = Relationship()

class Notification(SQLModel, table=True):
    """Table des notifications, généralement liées à une non-conformité."""
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id", nullable=False, index=True)
    project_id: int = Field(foreign_key="aiproject.id", nullable=False, index=True)
    nonconformite_id: Optional[int] = Field(foreign_key="nonconformite.id", nullable=True, index=True)
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow); updated_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = Field(default=False)
    project: Optional["AIProject"] = Relationship(back_populates="notifications")
    non_conformite: Optional["NonConformite"] = Relationship()

#----------MODÈLES MLOPS (RUNS, DATASETS, ARTÉFACTS)-------------
class ModelRun(SQLModel, table=True):
    """Table pour tracer un entraînement de modèle (un "run")."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow); started_at: Optional[datetime] = None; finished_at: Optional[datetime] = None
    status: str; logs: Optional[str] = None
    project: AIProject = Relationship(back_populates="model_runs")
    artifacts: List["ModelArtifact"] = Relationship(back_populates="run", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})

class DataSet(SQLModel, table=True):
    """Table des datasets, contenant le chemin vers le fichier de données et ses colonnes."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    kind: str; path: str; uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    columns: List[str] = Field(sa_column=Column(SQLiteJSON))
    project: "AIProject" = Relationship(back_populates="datasets", sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True})
    train_config: Optional["DataConfig"] = Relationship(back_populates="train_dataset", sa_relationship_kwargs={"foreign_keys": "[DataConfig.train_dataset_id]", "cascade": "all, delete-orphan", "single_parent": True, "uselist": False})
    test_config: Optional["DataConfig"] = Relationship(back_populates="test_dataset", sa_relationship_kwargs={"foreign_keys": "[DataConfig.test_dataset_id]", "cascade": "all, delete-orphan", "single_parent": True, "uselist": False})

class DataConfig(SQLModel, table=True):
    """Table de configuration des données, liant un dataset de train et de test avec la définition des features et de la cible."""
    id: Optional[int] = Field(default=None, primary_key=True)
    train_dataset_id: int = Field(sa_column=Column(ForeignKey("dataset.id", ondelete="CASCADE")))
    test_dataset_id: int = Field(sa_column=Column(ForeignKey("dataset.id", ondelete="CASCADE")))
    features: List[str] = Field(sa_column=Column(SQLiteJSON)); target: Optional[str] = Field(default=None, nullable=True)
    sensitive_attrs: List[str] = Field(sa_column=Column(SQLiteJSON))
    train_dataset: DataSet = Relationship(back_populates="train_config", sa_relationship_kwargs={"foreign_keys": "[DataConfig.train_dataset_id]"})
    test_dataset: DataSet = Relationship(back_populates="test_config", sa_relationship_kwargs={"foreign_keys": "[DataConfig.test_dataset_id]"})

class DataConfigCreate(BaseModel):
    train_dataset_id: int; test_dataset_id: int; features: List[str] = Field(min_items=1);
    target: Optional[str] = None; sensitive_attrs: List[str] = Field(default_factory=list)

class EvaluationRun(SQLModel, table=True):
    """Table pour tracer une évaluation de modèle."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    model_run_id: int = Field(foreign_key="modelrun.id")
    created_at: datetime = Field(default_factory=datetime.utcnow); started_at: Optional[datetime] = None; finished_at: Optional[datetime] = None
    status: str; metrics: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLiteJSON)); logs: Optional[str] = None
    project: "AIProject" = Relationship(back_populates="evaluation_runs")

class ModelArtifact(SQLModel, table=True):
    """Table des artéfacts produits par un run, typiquement le fichier du modèle entraîné."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="aiproject.id", index=True)
    model_run_id: int = Field(foreign_key="modelrun.id")
    path: str; format: str; size_bytes: int; created_at: datetime = Field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLiteJSON))
    project: "AIProject" = Relationship(back_populates="artifacts")
    run: "ModelRun" = Relationship(back_populates="artifacts")