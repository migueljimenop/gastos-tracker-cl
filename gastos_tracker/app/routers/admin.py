from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_superuser
from app.models import AuditLog, User
from app.schemas import AuditLogOut
from app.services.audit import record_audit_event

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_superuser)])


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(offset).limit(limit).all()
    response = [
        AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=json.loads(log.details or "{}"),
            created_at=log.created_at,
        )
        for log in logs
    ]

    record_audit_event(
        db,
        action="audit.viewed",
        entity_type="audit_log",
        entity_id=None,
        user_id=current_user.id,
        details={
            "filters": {
                "action": action,
                "entity_type": entity_type,
                "user_id": user_id,
            },
            "limit": limit,
            "offset": offset,
            "results": len(response),
        },
    )
    db.commit()
    return response