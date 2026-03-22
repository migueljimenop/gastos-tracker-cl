from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut, Token
from app.services.audit import record_audit_event
from app.services.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    user = User(username=data.username, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit_event(
        db,
        action="auth.register",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details={"username": user.username},
    )
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        record_audit_event(
            db,
            action="auth.login_failed",
            entity_type="user",
            entity_id=user.id if user else None,
            user_id=user.id if user else None,
            details={"username": form.username},
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    record_audit_event(
        db,
        action="auth.login_succeeded",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details={"username": user.username},
    )
    db.commit()
    return {"access_token": create_access_token(user.username), "token_type": "bearer"}
