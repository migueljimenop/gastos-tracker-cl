from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.models import BankSource, TransactionType


@dataclass
class RawTransaction:
    date: datetime
    description: str
    amount: Decimal
    transaction_type: TransactionType
    bank_source: BankSource
    external_id: Optional[str] = None


class BaseScraper(ABC):
    """Abstract base class for bank scrapers."""

    def __init__(self, rut: str, password: str):
        self.rut = rut
        self.password = password

    @abstractmethod
    async def fetch_transactions(self, months_back: int = 1) -> list[RawTransaction]:
        """Login to the bank portal and retrieve recent transactions."""
        ...

    def _normalize_rut(self, rut: str) -> str:
        """Remove dots and keep dash: 12.345.678-9 → 12345678-9"""
        return rut.replace(".", "")
