from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.models import BankSource, TransactionType


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    keywords: str = ""
    color: str = "#6366f1"


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[str] = None
    color: Optional[str] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    keywords: str
    color: str

    model_config = {"from_attributes": True}


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    date: datetime
    description: str
    amount: Decimal = Field(gt=0)
    transaction_type: TransactionType
    bank_source: BankSource
    external_id: Optional[str] = None
    notes: Optional[str] = None
    category_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    notes: Optional[str] = None


class TransactionOut(BaseModel):
    id: int
    date: datetime
    description: str
    amount: Decimal
    transaction_type: TransactionType
    bank_source: BankSource
    external_id: Optional[str]
    notes: Optional[str]
    category: Optional[CategoryOut]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Budget ────────────────────────────────────────────────────────────────────

class BudgetCreate(BaseModel):
    category_id: int
    monthly_limit: Decimal = Field(gt=0)
    alert_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class BudgetUpdate(BaseModel):
    monthly_limit: Optional[Decimal] = Field(default=None, gt=0)
    alert_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class BudgetOut(BaseModel):
    id: int
    category_id: int
    monthly_limit: Decimal
    alert_threshold: float
    category: CategoryOut

    model_config = {"from_attributes": True}


# ── Reports ───────────────────────────────────────────────────────────────────

class CategorySummary(BaseModel):
    category_id: Optional[int]
    category_name: str
    total: Decimal
    count: int


class MonthlyReport(BaseModel):
    year: int
    month: int
    total_spent: Decimal
    total_income: Decimal
    by_category: list[CategorySummary]


class BudgetAlert(BaseModel):
    budget_id: int
    category_name: str
    monthly_limit: Decimal
    spent_so_far: Decimal
    percentage_used: float
    is_exceeded: bool


# ── Importer ──────────────────────────────────────────────────────────────────

class ImportResult(BaseModel):
    bank: str
    filename: str
    transactions_found: int
    transactions_new: int
    transactions_skipped: int
    errors: list[str] = []


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


# ── Bulk delete ────────────────────────────────────────────────────────────────

class BulkDeleteRequest(BaseModel):
    ids: list[int]


# ── Scraper ───────────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    bank: BankSource
    months_back: int = Field(default=1, ge=1, le=12)


class ScrapeResult(BaseModel):
    bank: BankSource
    transactions_found: int
    transactions_new: int
    errors: list[str] = []
