from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class BankSource(str, enum.Enum):
    SANTANDER = "santander"
    FALABELLA = "falabella"
    MANUAL = "manual"


class TransactionType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    keywords: Mapped[str] = mapped_column(Text, default="")  # comma-separated keywords for auto-categorization
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")  # hex color for UI

    transactions: Mapped[List["Transaction"]] = relationship(back_populates="category")
    budgets: Mapped[List["Budget"]] = relationship(back_populates="category")

    def keyword_list(self) -> list[str]:
        return [k.strip().lower() for k in self.keywords.split(",") if k.strip()]


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    bank_source: Mapped[BankSource] = mapped_column(Enum(BankSource), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # banco's own ID to avoid duplicates
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category: Mapped[Optional["Category"]] = relationship(back_populates="transactions")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    alert_threshold: Mapped[float] = mapped_column(default=0.8)  # alert at 80% by default

    category: Mapped["Category"] = relationship(back_populates="budgets")
