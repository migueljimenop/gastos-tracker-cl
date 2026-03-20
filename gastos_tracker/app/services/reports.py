from datetime import datetime
from decimal import Decimal
from calendar import monthrange
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionType, Category
from app.schemas import MonthlyReport, CategorySummary


def build_monthly_report(year: int, month: int, db: Session) -> MonthlyReport:
    _, last_day = monthrange(year, month)
    start = datetime(year, month, 1)
    end = datetime(year, month, last_day, 23, 59, 59)

    base_q = db.query(Transaction).filter(Transaction.date >= start, Transaction.date <= end)

    total_spent = (
        base_q.filter(Transaction.transaction_type == TransactionType.DEBIT)
        .with_entities(func.sum(Transaction.amount))
        .scalar()
        or Decimal("0")
    )

    total_income = (
        base_q.filter(Transaction.transaction_type == TransactionType.CREDIT)
        .with_entities(func.sum(Transaction.amount))
        .scalar()
        or Decimal("0")
    )

    # Group debits by category
    rows = (
        base_q.filter(Transaction.transaction_type == TransactionType.DEBIT)
        .with_entities(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .group_by(Transaction.category_id)
        .all()
    )

    by_category: list[CategorySummary] = []
    for row in rows:
        category_name = "Sin categoría"
        if row.category_id:
            cat = db.get(Category, row.category_id)
            if cat:
                category_name = cat.name
        by_category.append(
            CategorySummary(
                category_id=row.category_id,
                category_name=category_name,
                total=row.total,
                count=row.count,
            )
        )

    by_category.sort(key=lambda x: x.total, reverse=True)

    return MonthlyReport(
        year=year,
        month=month,
        total_spent=total_spent,
        total_income=total_income,
        by_category=by_category,
    )
