#app/db.py

# `dotenv` est utilisé pour charger les variables d'environnement depuis un fichier `.env`.
# C'est très utile pour le développement local afin de ne pas coder en dur les secrets.
from dotenv import load_dotenv
import os
# SQLModel est la bibliothèque ORM principale, qui combine Pydantic et SQLAlchemy.
from sqlmodel import SQLModel, create_engine, Session
# `sessionmaker` est l'outil standard de SQLAlchemy pour créer des fabriques de sessions.
from sqlalchemy.orm import sessionmaker

# Charge les variables du fichier .env au démarrage du module.
load_dotenv()

# BLOC DE CONFIGURATION DE LA CONNEXION À LA BASE DE DONNÉES
# Cette section configure la manière dont l'application se connecte à la base de données.
# Récupère l'URL de la base de données depuis les variables d'environnement.
# Si la variable n'est pas définie, elle utilise par défaut une base de données SQLite locale,
# ce qui est très pratique pour le développement et les tests.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smia.db")

# Crée le moteur (engine) SQLModel. C'est l'objet de bas niveau qui gère
# le pool de connexions à la base de données.
engine = create_engine(
     DATABASE_URL,
     # `connect_args` est spécifique à SQLite. Il permet à FastAPI d'utiliser
     # la connexion à la base de données sur plusieurs threads, ce qui est nécessaire.
     connect_args={"check_same_thread": False},
     # `pool_pre_ping` est une bonne pratique qui vérifie que les connexions dans le pool
     # sont toujours actives avant de les utiliser, évitant les erreurs dues aux connexions expirées.
     pool_pre_ping=True,
 )

# BLOC DE LA FABRIQUE DE SESSIONS (SESSION FACTORY)
# `SessionLocal` n'est pas une session, mais une classe qui, lorsqu'elle est instanciée,
# crée une nouvelle session de base de données. C'est le point d'entrée pour toutes
# les opérations de base de données (lecture, écriture, etc.) dans l'application.
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,            # <- Spécifie qu'on utilise bien la classe Session de SQLModel.
    expire_on_commit=False,    # `expire_on_commit=False` est souvent utilisé pour que les objets
                               # restent accessibles même après la fin d'une transaction (commit).
)

# BLOC D'INITIALISATION DE LA BASE DE DONNÉES
def init_db():
    """
    Crée toutes les tables en base de données.
    Cette fonction inspecte tous les modèles qui héritent de `SQLModel`
    et crée les tables correspondantes si elles n'existent pas déjà.
    Elle est généralement appelée une seule fois au démarrage de l'application.
    """
    SQLModel.metadata.create_all(engine)