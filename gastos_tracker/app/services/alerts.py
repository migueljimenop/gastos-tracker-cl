from datetime import datetime
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Budget, Transaction, TransactionType
from app.schemas import BudgetAlert


def get_budget_alerts(db: Session) -> list[BudgetAlert]:
    """
    For the current calendar month, calculate spending per category
    and return budgets that have reached or exceeded their alert threshold.
    """
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    budgets = db.query(Budget).all()
    alerts: list[BudgetAlert] = []

    for budget in budgets:
        spent = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.category_id == budget.category_id,
                Transaction.transaction_type == TransactionType.DEBIT,
                Transaction.date >= month_start,
                Transaction.date <= now,
            )
            .scalar()
            or Decimal("0")
        )

        percentage = float(spent) / float(budget.monthly_limit) if budget.monthly_limit else 0.0
        is_exceeded = spent >= budget.monthly_limit

        if percentage >= budget.alert_threshold or is_exceeded:
            alerts.append(
                BudgetAlert(
                    budget_id=budget.id,
                    category_name=budget.category.name,
                    monthly_limit=budget.monthly_limit,
                    spent_so_far=spent,
                    percentage_used=round(percentage * 100, 2),
                    is_exceeded=is_exceeded,
                )
            )

    return alerts
