from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from datetime import datetime
from io import BytesIO

from app.scrapers.base import RawTransaction


@dataclass
class ImportResult:
    bank: str
    filename: str
    transactions_found: int = 0
    transactions_new: int = 0
    transactions_skipped: int = 0
    errors: list[str] = field(default_factory=list)


class BaseImporter(ABC):
    """Abstract base class for cartola (bank statement) file importers."""

    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".csv", ".xlsx", ".xls")

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> list[RawTransaction]:
        """
        Parse a cartola file and return a list of RawTransactions.
        Raises ValueError if the file format is not recognized.
        """
        ...

    def _detect_extension(self, filename: str) -> str:
        lower = filename.lower()
        for ext in self.SUPPORTED_EXTENSIONS:
            if lower.endswith(ext):
                return ext
        raise ValueError(f"Formato de archivo no soportado: {filename}. Use {', '.join(self.SUPPORTED_EXTENSIONS)}")

    @staticmethod
    def _parse_chilean_amount(raw: str) -> Decimal:
        """
        Convert Chilean-formatted number to Decimal.
        Examples: '1.234.567' → 1234567 | '1.234,56' → 1234.56 | '35.000' → 35000
        """
        cleaned = str(raw).strip().replace("$", "").replace(" ", "")
        if not cleaned or cleaned == "-":
            return Decimal("0")

        # Detect format: if there's a comma, treat it as decimal separator
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # Dots are thousand separators only
            cleaned = cleaned.replace(".", "")

        cleaned = cleaned.lstrip("+-")
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            raise ValueError(f"No se puede interpretar el monto: '{raw}'")

    @staticmethod
    def _parse_chilean_date(raw: str) -> datetime:
        """Parse dates in DD/MM/YYYY, DD-MM-YYYY or YYYY-MM-DD format."""
        raw = str(raw).strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        raise ValueError(f"No se puede interpretar la fecha: '{raw}'")

    @staticmethod
    def _read_dataframe(content: bytes, filename: str):
        """Load content into a pandas DataFrame, auto-detecting CSV vs Excel."""
        import pandas as pd

        lower = filename.lower()
        if lower.endswith(".csv"):
            # Try common encodings used by Chilean banks
            for encoding in ("latin-1", "utf-8", "cp1252"):
                try:
                    import io
                    return pd.read_csv(io.BytesIO(content), encoding=encoding, dtype=str)
                except Exception:
                    continue
            raise ValueError("No se pudo leer el CSV: prueba guardarlo con codificación UTF-8 o Latin-1")
        elif lower.endswith((".xlsx", ".xls")):
            return pd.read_excel(BytesIO(content), dtype=str)
        else:
            raise ValueError(f"Extensión no soportada: {filename}")
