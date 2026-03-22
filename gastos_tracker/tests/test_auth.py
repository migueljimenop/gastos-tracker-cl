from fastapi.testclient import TestClient

from app.models import AuditLog, User
from app.services.auth import hash_password


def test_register_creates_audit_log(client: TestClient, db):
    response = client.post("/auth/register", json={"username": "nuevo", "password": "secreto123"})

    assert response.status_code == 201
    user_id = response.json()["id"]

    log = db.query(AuditLog).filter(AuditLog.action == "auth.register", AuditLog.entity_id == user_id).first()
    assert log is not None
    assert log.user_id == user_id


def test_login_success_creates_audit_log(client: TestClient, db):
    user = User(username="login-ok", hashed_password=hash_password("clave123"), is_active=True, is_superuser=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post("/auth/login", data={"username": "login-ok", "password": "clave123"})

    assert response.status_code == 200
    log = db.query(AuditLog).filter(AuditLog.action == "auth.login_succeeded", AuditLog.user_id == user.id).first()
    assert log is not None


def test_login_failure_creates_audit_log(client: TestClient, db):
    user = User(username="login-fail", hashed_password=hash_password("clave123"), is_active=True, is_superuser=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post("/auth/login", data={"username": "login-fail", "password": "incorrecta"})

    assert response.status_code == 401
    log = db.query(AuditLog).filter(AuditLog.action == "auth.login_failed", AuditLog.user_id == user.id).first()
    assert log is not None