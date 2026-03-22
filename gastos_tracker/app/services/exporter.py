from __future__ import annotations

import io
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Transaction


def _get_transactions(db: Session, from_date: Optional[datetime], to_date: Optional[datetime], user_id: int):
    q = db.query(Transaction).filter(Transaction.user_id == user_id)
    if from_date:
        q = q.filter(Transaction.date >= from_date)
    if to_date:
        q = q.filter(Transaction.date <= to_date)
    return q.order_by(Transaction.date.desc()).all()


def _to_rows(transactions: list[Transaction]) -> list[dict]:
    return [
        {
            "Fecha": tx.date.strftime("%Y-%m-%d"),
            "Descripción": tx.description,
            "Monto": float(tx.amount),
            "Tipo": tx.transaction_type.value,
            "Banco": tx.bank_source.value,
            "Categoría": tx.category.name if tx.category else "",
            "Notas": tx.notes or "",
        }
        for tx in transactions
    ]


def export_to_csv(db: Session, from_date: Optional[datetime], to_date: Optional[datetime], user_id: int) -> str:
    import csv

    transactions = _get_transactions(db, from_date, to_date, user_id)
    rows = _to_rows(transactions)

    output = io.StringIO()
    if not rows:
        return ""

    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def export_to_excel(db: Session, from_date: Optional[datetime], to_date: Optional[datetime], user_id: int) -> bytes:
    import pandas as pd

    transactions = _get_transactions(db, from_date, to_date, user_id)
    rows = _to_rows(transactions)

    df = pd.DataFrame(rows) if rows else pd.DataFrame()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Gastos")

        if not df.empty:
            # Auto-fit columns
            worksheet = writer.sheets["Gastos"]
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                worksheet.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

    return output.getvalue()
