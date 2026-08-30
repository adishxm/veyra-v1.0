import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./veyra_audit.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency helper to yield database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()