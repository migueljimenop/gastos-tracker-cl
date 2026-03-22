"""
Santander Chile cartola importer.

Supported export formats from banco.santander.cl → Cuenta Corriente → Exportar:
  - Excel (.xlsx): Default download format
  - CSV: Alternative download

Expected column layout (Santander exports a few header rows before the table):

  Fecha       | Descripción                 | Cargo ($) | Abono ($) | Saldo ($)
  01/03/2026  | COMPRA SUPERMERCADO JUMBO   | 45.000    |           | 1.200.000
  05/03/2026  | ABONO SUELDO EMPRESA SA     |           | 2.500.000 | 3.700.000

Column names may include extra whitespace or vary slightly between downloads.
The importer searches flexibly for matching column names.
"""
from __future__ import annotations

import re
import pandas as pd

from app.importers.base import BaseImporter
from app.models import BankSource, TransactionType
from app.scrapers.base import RawTransaction


# Possible column name variants Santander uses
_DATE_COLS = {"fecha", "date"}
_DESC_COLS = {"descripción", "descripcion", "glosa", "detalle", "description"}
_DEBIT_COLS = {"cargo ($)", "cargo", "cargos", "débito", "debito", "debit", "cheques y otros cargos"}
_CREDIT_COLS = {"abono ($)", "abono", "abonos", "crédito", "credito", "credit", "depositos y otros abonos"}
_AMOUNT_COLS = {"monto", "amount", "importe"}  # fallback when there's only one amount column


def _find_col(columns: list[str], candidates: set[str]) -> str | None:
    for col in columns:
        if col.strip().lower() in candidates:
            return col
    return None


class SantanderImporter(BaseImporter):

    def parse(self, content: bytes, filename: str) -> list[RawTransaction]:
        self._detect_extension(filename)

        # Santander files have metadata rows before the actual table header.
        # Scan for the row that contains "Fecha" to find the real header.
        header_row = self._find_header_row_in_content(content, filename, {"fecha"})
        df = self._load_with_real_header(content, filename, header_row)

        # Normalize column names
        df.columns = [str(c).strip() for c in df.columns]
        cols = df.columns.tolist()

        date_col = _find_col(cols, _DATE_COLS)
        desc_col = _find_col(cols, _DESC_COLS)
        debit_col = _find_col(cols, _DEBIT_COLS)
        credit_col = _find_col(cols, _CREDIT_COLS)
        amount_col = _find_col(cols, _AMOUNT_COLS)

        if not date_col or not desc_col:
            raise ValueError(
                f"No se encontraron columnas de fecha/descripción en la cartola Santander. "
                f"Columnas detectadas: {cols}"
            )

        if not debit_col and not credit_col and not amount_col:
            raise ValueError(
                f"No se encontró columna de montos en la cartola Santander. "
                f"Columnas detectadas: {cols}"
            )

        # Extract year from filename for partial-date rows (e.g. "02/03" without year)
        year_match = re.search(r'\b(20\d{2})\b', filename)
        filename_year = int(year_match.group(1)) if year_match else None

        transactions: list[RawTransaction] = []

        for _, row in df.iterrows():
            date_raw = str(row.get(date_col, "")).strip()
            desc_raw = str(row.get(desc_col, "")).strip()

            # Skip empty or total rows
            if not date_raw or date_raw.lower() in ("nan", "", "fecha", "totales", "total"):
                continue
            if not desc_raw or desc_raw.lower() in ("nan", ""):
                continue

            try:
                date = self._parse_chilean_date(date_raw, year=filename_year)
            except ValueError:
                continue  # Skip non-date rows (e.g. trailing summary rows)

            # Determine amount and direction
            if debit_col and credit_col:
                debit_raw = str(row.get(debit_col, "")).strip()
                credit_raw = str(row.get(credit_col, "")).strip()

                debit_val = self._parse_chilean_amount(debit_raw) if debit_raw not in ("nan", "", "-") else None
                credit_val = self._parse_chilean_amount(credit_raw) if credit_raw not in ("nan", "", "-") else None

                if debit_val and debit_val > 0:
                    amount = debit_val
                    tx_type = TransactionType.DEBIT
                elif credit_val and credit_val > 0:
                    amount = credit_val
                    tx_type = TransactionType.CREDIT
                else:
                    continue  # Row with no movement
            elif amount_col:
                amount_raw = str(row.get(amount_col, "")).strip()
                if amount_raw in ("nan", ""):
                    continue
                raw_signed = amount_raw.replace("$", "").replace(" ", "")
                is_negative = raw_signed.startswith("-")
                amount = self._parse_chilean_amount(amount_raw)
                if amount == 0:
                    continue
                tx_type = TransactionType.CREDIT if is_negative else TransactionType.DEBIT
            else:
                continue

            ext_id = f"santander-{date.date()}-{desc_raw[:40]}-{amount}"
            transactions.append(
                RawTransaction(
                    date=date,
                    description=desc_raw,
                    amount=amount,
                    transaction_type=tx_type,
                    bank_source=BankSource.SANTANDER,
                    external_id=ext_id,
                )
            )

        return transactions

    def _find_header_row(self, df: pd.DataFrame) -> int:
        """Return the index of the row that contains 'Fecha' (the real table header)."""
        for i, row in df.iterrows():
            for cell in row.values:
                if str(cell).strip().lower() == "fecha":
                    return int(str(i))
        return 0  # If not found, assume first row is the header

    def _load_with_real_header(self, content: bytes, filename: str, header_row: int) -> pd.DataFrame:
        """Reload the file using the detected header row."""
        from io import BytesIO
        import pandas as pd

        lower = filename.lower()
        if lower.endswith(".csv"):
            # Use skiprows + header=0 instead of header=N to avoid the C parser
            # failing on metadata rows that have fewer columns than the data table.
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
