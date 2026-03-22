from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Transaction, BankSource, Category, User
from app.schemas import TransactionCreate, TransactionUpdate, TransactionOut, BulkDeleteRequest
from app.services.audit import record_audit_event
from app.services.categorizer import auto_categorize

router = APIRouter(prefix="/transactions", tags=["transactions"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[TransactionOut])
def list_transactions(
    bank: Optional[BankSource] = None,
    category_id: Optional[int] = None,
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if bank:
        q = q.filter(Transaction.bank_source == bank)
    if category_id is not None:
        q = q.filter(Transaction.category_id == category_id)
    if from_date:
        q = q.filter(Transaction.date >= from_date)
    if to_date:
        q = q.filter(Transaction.date <= to_date)
    return q.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()


@router.post("/", response_model=TransactionOut, status_code=201)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == data.category_id, Category.user_id == current_user.id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    tx = Transaction(**data.model_dump(), user_id=current_user.id)
    if tx.category_id is None:
        tx.category_id = auto_categorize(tx.description, db, current_user.id)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    record_audit_event(
        db,
        action="transaction.created",
        entity_type="transaction",
        entity_id=tx.id,
        user_id=current_user.id,
        details={
            "bank_source": tx.bank_source,
            "category_id": tx.category_id,
            "transaction_type": tx.transaction_type,
        },
    )
    db.commit()
    return tx


@router.get("/{tx_id}", response_model=TransactionOut)
def get_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.patch("/{tx_id}", response_model=TransactionOut)
def update_transaction(
    tx_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if data.category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == data.category_id, Category.user_id == current_user.id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    record_audit_event(
        db,
        action="transaction.updated",
        entity_type="transaction",
        entity_id=tx.id,
        user_id=current_user.id,
        details={"changed_fields": sorted(data.model_dump(exclude_none=True).keys())},
    )
    db.commit()
    return tx


@router.delete("/bulk", status_code=204)
def bulk_delete(
    data: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted_ids = [row[0] for row in db.query(Transaction.id).filter(
        Transaction.user_id == current_user.id,
        Transaction.id.in_(data.ids),
    ).all()]
    for tx_id in deleted_ids:
        record_audit_event(
            db,
            action="transaction.deleted",
            entity_type="transaction",
            entity_id=tx_id,
            user_id=current_user.id,
            details={"bulk": True},
        )
    db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.id.in_(data.ids),
    ).delete(synchronize_session=False)
    db.commit()


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    record_audit_event(
        db,
        action="transaction.deleted",
        entity_type="transaction",
        entity_id=tx.id,
        user_id=current_user.id,
        details={"bulk": False},
    )
    db.delete(tx)
    db.commit()
