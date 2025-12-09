"""Pydantic data models for Thai bank statement parsing."""

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """A single bank transaction."""

    date: dt.date
    time: dt.time | None = None
    description: str
    channel: str | None = None  # K PLUS, EDC, ATM, mPhone, Gtway, BR0369, etc.
    withdrawal: Decimal | None = None
    deposit: Decimal | None = None
    balance: Decimal
    reference: str | None = None
    check_number: str | None = None  # BBL: Chq.No. field


class Statement(BaseModel):
    """A single bank statement from one PDF."""

    account_number: str  # XXX-X-XXXXX-X format
    account_name: str | None = None
    statement_period_start: dt.date
    statement_period_end: dt.date
    opening_balance: Decimal
    closing_balance: Decimal
    transactions: list[Transaction] = Field(default_factory=list)
    source_pdf: str
    language: str = "unknown"  # "en", "th", or "unknown"
    bank: str = "unknown"  # "kbank", "bbl", or "unknown"
    branch: str | None = None  # e.g., "0369 KUMPHAWAPI BRANCH"
    currency: str = "THB"  # Currency code


class Account(BaseModel):
    """Consolidated account with all statements and deduplicated transactions."""

    account_number: str
    account_name: str | None = None
    statements: list[Statement] = Field(default_factory=list)
    all_transactions: list[Transaction] = Field(default_factory=list)  # Deduplicated, sorted

    def add_statement(self, statement: Statement) -> None:
        """Add a statement and merge transactions."""
        self.statements.append(statement)
        if not self.account_name and statement.account_name:
            self.account_name = statement.account_name
        self._merge_transactions()

    def _merge_transactions(self) -> None:
        """Merge and deduplicate transactions from all statements."""
        all_txns: set[Transaction] = set()
        for stmt in self.statements:
            for txn in stmt.transactions:
                all_txns.add(txn)
        # Sort by date, then time
        self.all_transactions = sorted(
            all_txns,
            key=lambda t: (t.date, t.time or dt.time(0, 0)),
        )
