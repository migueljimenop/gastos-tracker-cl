"""
Falabella CMR cartola importer.

Supported export formats from www.falabella.com → Mi Cuenta → CMR → Estado de Cuenta → Descargar:
  - Excel (.xlsx): Main download format
  - CSV: Alternative

Two common layouts depending on the download type:

Layout A — "Movimientos" (single signed amount column):
  Fecha       | Descripción                  | Monto
  15/03/2026  | COMPRA FALABELLA ONLINE      | -35.000
  20/03/2026  | PAGO CUOTA MARZO             | 100.000

Layout B — "Cartola detallada" (separate Cargo / Abono columns):
  Fecha       | Descripción                  | Cargo   | Abono
  15/03/2026  | COMPRA FALABELLA ONLINE      | 35.000  |
  20/03/2026  | PAGO CUOTA MARZO             |         | 100.000

In Layout A a negative amount = purchase (DEBIT), positive = payment (CREDIT).
In Layout B Cargo = DEBIT, Abono = CREDIT.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd

from app.importers.base import BaseImporter
from app.models import BankSource, TransactionType
from app.scrapers.base import RawTransaction


_DATE_COLS = {"fecha", "fecha transacción", "fecha transaccion", "date"}
_DESC_COLS = {"descripción", "descripcion", "glosa", "detalle", "comercio", "description"}
_AMOUNT_COLS = {"monto", "amount", "importe", "valor"}
_DEBIT_COLS = {"cargo", "cargos", "débito", "debito", "debit"}
_CREDIT_COLS = {"abono", "abonos", "crédito", "credito", "pago", "credit"}


def _find_col(columns: list[str], candidates: set[str]) -> str | None:
    for col in columns:
        if col.strip().lower() in candidates:
            return col
    return None


class FalabellaImporter(BaseImporter):

    def parse(self, content: bytes, filename: str) -> list[RawTransaction]:
        self._detect_extension(filename)

        header_row = self._find_header_row_in_content(
            content, filename, {"fecha", "descripción", "descripcion"}
        )
        df = self._load_with_real_header(content, filename, header_row)

        df.columns = [str(c).strip() for c in df.columns]
        cols = df.columns.tolist()

        date_col = _find_col(cols, _DATE_COLS)
        desc_col = _find_col(cols, _DESC_COLS)
        amount_col = _find_col(cols, _AMOUNT_COLS)
        debit_col = _find_col(cols, _DEBIT_COLS)
        credit_col = _find_col(cols, _CREDIT_COLS)

        if not date_col or not desc_col:
            raise ValueError(
                f"No se encontraron columnas de fecha/descripción en la cartola Falabella. "
                f"Columnas detectadas: {cols}"
            )

        if not amount_col and not debit_col and not credit_col:
            raise ValueError(
                f"No se encontró columna de montos en la cartola Falabella. "
                f"Columnas detectadas: {cols}"
            )

        transactions: list[RawTransaction] = []

        for _, row in df.iterrows():
            date_raw = str(row.get(date_col, "")).strip()
            desc_raw = str(row.get(desc_col, "")).strip()

            if not date_raw or date_raw.lower() in ("nan", "", "fecha", "fecha transacción"):
                continue
            if not desc_raw or desc_raw.lower() in ("nan", ""):
                continue

            try:
                date = self._parse_chilean_date(date_raw)
            except ValueError:
                continue

            # ── Layout B: separate Cargo/Abono columns ──
            if debit_col and credit_col:
                debit_raw = str(row.get(debit_col, "")).strip()
                credit_raw = str(row.get(credit_col, "")).strip()

                debit_val = self._parse_chilean_amount(debit_raw) if debit_raw not in ("nan", "", "-") else None
                credit_val = self._parse_chilean_amount(credit_raw) if credit_raw not in ("nan", "", "-") else None

                if debit_val and debit_val > 0:
                    amount, tx_type = debit_val, TransactionType.DEBIT
                elif credit_val and credit_val > 0:
                    amount, tx_type = credit_val, TransactionType.CREDIT
                else:
                    continue

            # ── Layout A: single signed Monto column ──
            elif amount_col:
                amount_raw = str(row.get(amount_col, "")).strip()
                if amount_raw in ("nan", ""):
                    continue

                # Detect sign before stripping symbols
                cleaned = amount_raw.replace("$", "").replace(" ", "")
                is_negative = cleaned.startswith("-")
                amount = self._parse_chilean_amount(amount_raw)
                if amount == 0:
                    continue
                # In Falabella Layout A: negative = purchase (DEBIT), positive = payment (CREDIT)
                tx_type = TransactionType.DEBIT if is_negative else TransactionType.CREDIT

            else:
                continue

            ext_id = f"falabella-{date.date()}-{desc_raw[:40]}-{amount}"
            transactions.append(
                RawTransaction(
                    date=date,
                    description=desc_raw,
                    amount=amount,
                    transaction_type=tx_type,
                    bank_source=BankSource.FALABELLA,
                    external_id=ext_id,
                )
            )

        return transactions

    def _find_header_row(self, df: pd.DataFrame) -> int:
        """Find the row that contains 'Fecha' or 'Descripción' as the real table header."""
        for i, row in df.iterrows():
            for cell in row.values:
                if str(cell).strip().lower() in ("fecha", "descripción", "descripcion"):
                    return int(str(i))
        return 0

    def _load_with_real_header(self, content: bytes, filename: str, header_row: int) -> pd.DataFrame:
        lower = filename.lower()
        if lower.endswith(".csv"):
            for encoding in ("latin-1", "utf-8", "cp1252"):
                try:
                    import io
                    return pd.read_csv(
                        io.BytesIO(content),
                        encoding=encoding,
                        skiprows=header_row,
                        header=0,
                        dtype=str,
                    )
                except Exception:
                    continue
        return pd.read_excel(BytesIO(content), header=header_row, dtype=str)
