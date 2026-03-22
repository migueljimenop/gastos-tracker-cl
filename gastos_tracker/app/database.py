from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app import models  # noqa: F401 - ensures models are registered
    Base.metadata.create_all(bind=engine)
    _migrate_add_user_id()


def _migrate_add_user_id():
    """Adds user_id column to transactions if it doesn't exist yet (SQLite migration)."""
    with engine.connect() as conn:
        from sqlalchemy import text
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(transactions)"))]
        if "user_id" not in cols:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN user_id INTEGER REFERENCES users(id)"))
