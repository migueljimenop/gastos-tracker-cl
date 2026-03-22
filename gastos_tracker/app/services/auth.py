"""
Auth utilities using stdlib only (hmac + hashlib) for JWT HS256,
avoiding external cryptography dependencies.
"""
import base64
import hashlib
import hmac
import json
import time

from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def create_access_token(username: str) -> str:
    header  = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "sub": username,
        "exp": int(time.time()) + settings.JWT_EXPIRE_HOURS * 3600,
    }).encode())
    signing_input = f"{header}.{payload}"
    sig = _b64url_encode(hmac.new(
        settings.SECRET_KEY.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest())
    return f"{signing_input}.{sig}"


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises ValueError if invalid or expired."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("Token malformado")

    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = _b64url_encode(hmac.new(
        settings.SECRET_KEY.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest())

    if not hmac.compare_digest(expected_sig, sig_b64):
        raise ValueError("Firma inválida")

    payload = json.loads(_b64url_decode(payload_b64))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expirado")

    return payload
