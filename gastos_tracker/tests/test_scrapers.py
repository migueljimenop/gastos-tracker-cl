"""
Tests for the scraper base class and parser logic.
Actual network calls to bank portals are not tested here
(they require live credentials and are environment-dependent).
"""
import pytest
from datetime import datetime
from decimal import Decimal

from app.scrapers.base import BaseScraper, RawTransaction
from app.models import BankSource, TransactionType


class DummyScraper(BaseScraper):
    """Concrete scraper for testing the base class."""

    async def fetch_transactions(self, months_back: int = 1) -> list[RawTransaction]:
        return [
            RawTransaction(
                date=datetime(2026, 3, 15),
                description="Test transaction",
                amount=Decimal("10000"),
                transaction_type=TransactionType.DEBIT,
                bank_source=BankSource.SANTANDER,
                external_id="test-001",
            )
        ]


def test_normalize_rut_removes_dots():
    scraper = DummyScraper("12.345.678-9", "password")
    assert scraper._normalize_rut("12.345.678-9") == "12345678-9"


def test_normalize_rut_no_dots():
    scraper = DummyScraper("12345678-9", "password")
    assert scraper._normalize_rut("12345678-9") == "12345678-9"


@pytest.mark.asyncio
async def test_dummy_scraper_returns_transactions():
    scraper = DummyScraper("12345678-9", "pass")
    transactions = await scraper.fetch_transactions()
    assert len(transactions) == 1
    assert transactions[0].external_id == "test-001"
    assert transactions[0].amount == Decimal("10000")
