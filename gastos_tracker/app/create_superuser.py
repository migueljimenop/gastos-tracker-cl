from __future__ import annotations

import argparse

from sqlalchemy import inspect, text

from app.database import SessionLocal, create_tables, engine
from app.models import User
from app.services.auth import hash_password


def ensure_user_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        create_tables()
        inspector = inspect(engine)

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_superuser" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT 0")
            )


def create_or_promote_superuser(username: str, password: str) -> tuple[User, bool]:
    ensure_user_columns()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        created = False

        if user is None:
            user = User(
                username=username,
                hashed_password=hash_password(password),
                is_active=True,
                is_superuser=True,
            )
            db.add(user)
            created = True
        else:
            user.hashed_password = hash_password(password)
            user.is_active = True
            user.is_superuser = True

        db.commit()
        db.refresh(user)
        return user, created
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear o promover un superusuario")
    parser.add_argument("--username", required=True, help="Nombre de usuario del administrador")
    parser.add_argument("--password", required=True, help="Contrasena del administrador")
    args = parser.parse_args()

    user, created = create_or_promote_superuser(args.username, args.password)
    action = "creado" if created else "actualizado"
    print(f"Superusuario {action}: {user.username}")


if __name__ == "__main__":
    main()