from sqlalchemy import create_engine, inspect, text
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
    ensure_schema_updates()


def ensure_schema_updates():
    inspector = inspect(engine)

    existing_tables = set(inspector.get_table_names())
    if "users" in existing_tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "is_superuser" not in user_columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT 0")
                )

    for table_name in ("categories", "transactions", "budgets"):
        if table_name not in existing_tables:
            continue
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "user_id" not in columns:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER"))

    if "users" not in existing_tables:
        return

    with engine.begin() as connection:
        user_ids = [row[0] for row in connection.execute(text("SELECT id FROM users ORDER BY id"))]
        if len(user_ids) != 1:
            return

        owner_id = user_ids[0]
        for table_name in ("categories", "transactions", "budgets"):
            if table_name in existing_tables:
                connection.execute(
                    text(f"UPDATE {table_name} SET user_id = :owner_id WHERE user_id IS NULL"),
                    {"owner_id": owner_id},
                )
