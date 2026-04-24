"""
Tests for the auth endpoints and auth service utilities.
"""
import pytest
from fastapi.testclient import TestClient

from app.models import User
from app.services.auth import hash_password, verify_password, create_access_token, decode_token


# ── Auth service unit tests ────────────────────────────────────────────────────

class TestAuthService:
    def test_hash_and_verify_correct_password(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_create_and_decode_token(self):
        token = create_access_token("alice")
        payload = decode_token(token)
        assert payload["sub"] == "alice"
        assert "exp" in payload

    def test_decode_tampered_signature_raises(self):
        token = create_access_token("alice")
        parts = token.split(".")
        tampered = ".".join(parts[:-1]) + ".invalidsig"
        with pytest.raises(ValueError, match="inválida"):
            decode_token(tampered)

    def test_decode_malformed_token_raises(self):
        with pytest.raises(ValueError, match="malformado"):
            decode_token("not.a.valid.jwt.token.with.too.many.parts")

    def test_decode_expired_token_raises(self):
        import time
        import json
        import base64
        import hmac
        import hashlib
        from app.config import settings

        def b64enc(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header = b64enc(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = b64enc(json.dumps({"sub": "alice", "exp": int(time.time()) - 10}).encode())
        signing_input = f"{header}.{payload}"
        sig = b64enc(hmac.new(
            settings.SECRET_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest())
        expired_token = f"{signing_input}.{sig}"

        with pytest.raises(ValueError, match="expirado"):
            decode_token(expired_token)


# ── Auth endpoint tests ────────────────────────────────────────────────────────

class TestAuthEndpoints:
    def test_register_new_user(self, client: TestClient):
        resp = client.post("/auth/register", json={"username": "newuser", "password": "pass123"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_username_returns_409(self, client: TestClient):
        client.post("/auth/register", json={"username": "dupuser", "password": "pass123"})
        resp = client.post("/auth/register", json={"username": "dupuser", "password": "other"})
        assert resp.status_code == 409

    def test_login_valid_credentials_returns_token(self, client: TestClient, db):
        user = User(
            username="loginuser",
            hashed_password=hash_password("mypassword"),
            is_active=True,
        )
        db.add(user)
        db.commit()

        resp = client.post("/auth/login", data={"username": "loginuser", "password": "mypassword"})
        assert resp.status_code == 200
        token_data = resp.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client: TestClient, db):
        user = User(
            username="someuser",
            hashed_password=hash_password("correct"),
            is_active=True,
        )
        db.add(user)
        db.commit()

        resp = client.post("/auth/login", data={"username": "someuser", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unknown_user_returns_401(self, client: TestClient):
        resp = client.post("/auth/login", data={"username": "nobody", "password": "pass"})
        assert resp.status_code == 401

    def test_register_then_login_token_is_decodable(self, client: TestClient, db):
        client.post("/auth/register", json={"username": "roundtrip", "password": "p@ss"})
        user = db.query(User).filter(User.username == "roundtrip").first()
        assert user is not None

        resp = client.post("/auth/login", data={"username": "roundtrip", "password": "p@ss"})
        token = resp.json()["access_token"]
        payload = decode_token(token)
        assert payload["sub"] == "roundtrip"
