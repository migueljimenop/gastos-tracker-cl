"""
Tests for the Santander and Falabella cartola importers.
Uses in-memory CSV content to simulate real bank exports.
"""
import io
import pytest
from decimal import Decimal

from app.importers.santander import SantanderImporter
from app.importers.falabella import FalabellaImporter
from app.importers.base import BaseImporter
from app.models import TransactionType, BankSource


# ── Helpers ────────────────────────────────────────────────────────────────────

def csv_bytes(text: str) -> bytes:
    return text.strip().encode("latin-1")


# ── BaseImporter helpers ───────────────────────────────────────────────────────

class TestBaseHelpers:
    def setup_method(self):
        # Use SantanderImporter to access inherited helpers
        self.imp = SantanderImporter()

    def test_parse_chilean_amount_thousands_dot(self):
        assert self.imp._parse_chilean_amount("1.234.567") == Decimal("1234567")

    def test_parse_chilean_amount_with_decimal_comma(self):
        assert self.imp._parse_chilean_amount("1.234,56") == Decimal("1234.56")

    def test_parse_chilean_amount_with_dollar(self):
        assert self.imp._parse_chilean_amount("$ 45.000") == Decimal("45000")

    def test_parse_chilean_amount_negative(self):
        assert self.imp._parse_chilean_amount("-35.000") == Decimal("35000")

    def test_parse_chilean_amount_empty(self):
        assert self.imp._parse_chilean_amount("") == Decimal("0")
        assert self.imp._parse_chilean_amount("-") == Decimal("0")

    def test_parse_chilean_date_slash(self):
        from datetime import datetime
        dt = self.imp._parse_chilean_date("15/03/2026")
        assert dt == datetime(2026, 3, 15)

    def test_parse_chilean_date_dash(self):
        from datetime import datetime
        dt = self.imp._parse_chilean_date("15-03-2026")
        assert dt == datetime(2026, 3, 15)

    def test_parse_chilean_date_iso(self):
        from datetime import datetime
        dt = self.imp._parse_chilean_date("2026-03-15")
        assert dt == datetime(2026, 3, 15)

    def test_parse_chilean_date_invalid(self):
        with pytest.raises(ValueError):
            self.imp._parse_chilean_date("not-a-date")

    def test_detect_extension_unsupported(self):
        with pytest.raises(ValueError, match="no soportado"):
            self.imp._detect_extension("file.pdf")


# ── Santander Importer ─────────────────────────────────────────────────────────

SANTANDER_CSV_CARGO_ABONO = """\
Cuenta Corriente N° 000123456
Del 01/03/2026 al 31/03/2026

Fecha,Descripción,Cargo ($),Abono ($),Saldo ($)
15/03/2026,COMPRA SUPERMERCADO JUMBO,45.000,,1.200.000
20/03/2026,ABONO SUELDO EMPRESA SA,,2.500.000,3.700.000
22/03/2026,PAGO NETFLIX,15.990,,3.684.010
"""

SANTANDER_CSV_SINGLE_AMOUNT = """\
Fecha,Descripción,Monto
15/03/2026,COMPRA UBER,12.500
01/03/2026,ABONO TRANSFERENCIA,-100.000
"""


class TestSantanderImporter:
    def setup_method(self):
        self.importer = SantanderImporter()

    def test_parse_cargo_abono_layout(self):
        txs = self.importer.parse(csv_bytes(SANTANDER_CSV_CARGO_ABONO), "cartola.csv")
        assert len(txs) == 3

    def test_debit_transaction(self):
        txs = self.importer.parse(csv_bytes(SANTANDER_CSV_CARGO_ABONO), "cartola.csv")
        supermercado = next(t for t in txs if "JUMBO" in t.description)
        assert supermercado.transaction_type == TransactionType.DEBIT
        assert supermercado.amount == Decimal("45000")
        assert supermercado.bank_source == BankSource.SANTANDER

    def test_credit_transaction(self):
        txs = self.importer.parse(csv_bytes(SANTANDER_CSV_CARGO_ABONO), "cartola.csv")
        sueldo = next(t for t in txs if "SUELDO" in t.description)
        assert sueldo.transaction_type == TransactionType.CREDIT
        assert sueldo.amount == Decimal("2500000")

    def test_date_parsing(self):
        from datetime import datetime
        txs = self.importer.parse(csv_bytes(SANTANDER_CSV_CARGO_ABONO), "cartola.csv")
        dates = {t.date for t in txs}
        assert datetime(2026, 3, 15) in dates
        assert datetime(2026, 3, 20) in dates

    def test_external_id_is_unique_per_transaction(self):
        txs = self.importer.parse(csv_bytes(SANTANDER_CSV_CARGO_ABONO), "cartola.csv")
        ids = [t.external_id for t in txs]
        assert len(ids) == len(set(ids)), "external_ids must be unique"

    def test_single_amount_column_debit(self):
        txs = self.importer.parse(csv_bytes(SANTANDER_CSV_SINGLE_AMOUNT), "movimientos.csv")
        uber = next(t for t in txs if "UBER" in t.description)
        assert uber.transaction_type == TransactionType.DEBIT
        assert uber.amount == Decimal("12500")

    def test_single_amount_column_credit(self):
        txs = self.importer.parse(csv_bytes(SANTANDER_CSV_SINGLE_AMOUNT), "movimientos.csv")
        abono = next(t for t in txs if "TRANSFERENCIA" in t.description)
        assert abono.transaction_type == TransactionType.CREDIT

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError):
            self.importer.parse(b"data", "cartola.pdf")

    def test_missing_date_column_raises(self):
        bad_csv = csv_bytes("Columna1,Columna2\nval1,val2\n")
        with pytest.raises(ValueError, match="fecha"):
            self.importer.parse(bad_csv, "bad.csv")


# ── Falabella Importer ─────────────────────────────────────────────────────────

FALABELLA_CSV_SIGNED = """\
CMR Falabella - Estado de Cuenta
Número de cuenta: 1234-5678

Fecha,Descripción,Monto
15/03/2026,COMPRA FALABELLA ONLINE,-35.000
20/03/2026,PAGO CUOTA MARZO,100.000
25/03/2026,COMPRA RAPPI DELIVERY,-18.500
"""

FALABELLA_CSV_CARGO_ABONO = """\
Fecha,Descripción,Cargo,Abono
15/03/2026,COMPRA RIPLEY ONLINE,35.000,
20/03/2026,PAGO AUTOMATICO,,100.000
"""


class TestFalabellaImporter:
    def setup_method(self):
        self.importer = FalabellaImporter()

    def test_parse_signed_amount_layout(self):
        txs = self.importer.parse(csv_bytes(FALABELLA_CSV_SIGNED), "estado.csv")
        assert len(txs) == 3

    def test_negative_is_debit(self):
        txs = self.importer.parse(csv_bytes(FALABELLA_CSV_SIGNED), "estado.csv")
        compra = next(t for t in txs if "FALABELLA ONLINE" in t.description)
        assert compra.transaction_type == TransactionType.DEBIT
        assert compra.amount == Decimal("35000")
        assert compra.bank_source == BankSource.FALABELLA

    def test_positive_is_credit(self):
        txs = self.importer.parse(csv_bytes(FALABELLA_CSV_SIGNED), "estado.csv")
        pago = next(t for t in txs if "PAGO" in t.description)
        assert pago.transaction_type == TransactionType.CREDIT
        assert pago.amount == Decimal("100000")

    def test_cargo_abono_layout(self):
        txs = self.importer.parse(csv_bytes(FALABELLA_CSV_CARGO_ABONO), "cartola.csv")
        assert len(txs) == 2
        cargo = next(t for t in txs if "RIPLEY" in t.description)
        assert cargo.transaction_type == TransactionType.DEBIT
        abono = next(t for t in txs if "AUTOMATICO" in t.description)
        assert abono.transaction_type == TransactionType.CREDIT

    def test_external_id_uniqueness(self):
        txs = self.importer.parse(csv_bytes(FALABELLA_CSV_SIGNED), "estado.csv")
        ids = [t.external_id for t in txs]
        assert len(ids) == len(set(ids))

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError):
            self.importer.parse(b"data", "cartola.txt")


# ── Upload endpoint integration tests ─────────────────────────────────────────

class TestImportEndpoints:
    def test_import_santander_csv(self, client):
        file_content = csv_bytes(SANTANDER_CSV_CARGO_ABONO)
        resp = client.post(
            "/import/santander",
            files={"file": ("cartola_santander.csv", file_content, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transactions_found"] == 3
        assert data["transactions_new"] == 3
        assert data["transactions_skipped"] == 0
        assert data["errors"] == []

    def test_import_santander_deduplication(self, client):
        file_content = csv_bytes(SANTANDER_CSV_CARGO_ABONO)
        client.post("/import/santander", files={"file": ("c.csv", file_content, "text/csv")})
        # Upload the same file again
        resp = client.post("/import/santander", files={"file": ("c.csv", file_content, "text/csv")})
        data = resp.json()
        assert data["transactions_new"] == 0
        assert data["transactions_skipped"] == 3

    def test_import_falabella_csv(self, client):
        file_content = csv_bytes(FALABELLA_CSV_SIGNED)
        resp = client.post(
            "/import/falabella",
            files={"file": ("estado_falabella.csv", file_content, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transactions_found"] == 3
        assert data["transactions_new"] == 3

    def test_import_invalid_format_returns_422(self, client):
        bad_content = b"esto,no,es,una,cartola\nfoo,bar,baz\n"
        resp = client.post(
            "/import/santander",
            files={"file": ("malo.csv", bad_content, "text/csv")},
        )
        assert resp.status_code == 422

    def test_import_transactions_are_auto_categorized(self, client):
        # Create a category that matches "JUMBO"
        client.post("/categories/", json={"name": "Supermercado", "keywords": "jumbo,lider,unimarc"})

        file_content = csv_bytes(SANTANDER_CSV_CARGO_ABONO)
        client.post("/import/santander", files={"file": ("c.csv", file_content, "text/csv")})

        txs = client.get("/transactions/").json()
        jumbo = next(t for t in txs if "JUMBO" in t["description"])
        assert jumbo["category"]["name"] == "Supermercado"
