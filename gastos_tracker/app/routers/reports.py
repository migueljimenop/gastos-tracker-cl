from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.reports import build_monthly_report
from app.services.audit import record_audit_event
from app.services.exporter import export_to_csv, export_to_excel
from app.schemas import MonthlyReport

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("/monthly", response_model=MonthlyReport)
def monthly_report(
    year: int = Query(default_factory=lambda: datetime.now().year),
    month: int = Query(default_factory=lambda: datetime.now().month, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_monthly_report(year, month, db, current_user.id)


@router.get("/export/csv")
def export_csv(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = export_to_csv(db, from_date, to_date, current_user.id)
    record_audit_event(
        db,
        action="report.exported_csv",
        entity_type="report",
        entity_id=None,
        user_id=current_user.id,
        details={"from_date": from_date, "to_date": to_date},
    )
    db.commit()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gastos.csv"},
    )


@router.get("/export/excel")
def export_excel(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = export_to_excel(db, from_date, to_date, current_user.id)
    record_audit_event(
        db,
        action="report.exported_excel",
        entity_type="report",
        entity_id=None,
        user_id=current_user.id,
        details={"from_date": from_date, "to_date": to_date},
    )
    db.commit()
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=gastos.xlsx"},
    )
