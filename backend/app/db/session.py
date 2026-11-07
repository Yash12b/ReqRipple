from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Determine absolute db url if relative sqlite path is used
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
    rel_path = db_url.replace("sqlite:///", "")
    backend_root = Path(__file__).resolve().parent.parent.parent
    abs_path = (backend_root / rel_path).resolve()
    db_url = f"sqlite:///{abs_path}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
)

if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
