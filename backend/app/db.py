#app/db.py
from dotenv import load_dotenv
import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smia.db")
engine = create_engine(
     DATABASE_URL,
     connect_args={"check_same_thread": False},
     pool_pre_ping=True,
 )

# Factory de sessions SQLModel (expire_on_commit=False pour ne pas expirer les objets)
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,            # <- important : c’est le Session de SQLModel
)

def init_db():
    SQLModel.metadata.create_all(engine)
