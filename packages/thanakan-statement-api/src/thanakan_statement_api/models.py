"""Request/Response Pydantic models for the API."""

import datetime as dt

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    """Transaction with string-serialized Decimal fields for JSON."""

    date: dt.date
    time: dt.time | None = None
    description: str
    channel: str | None = None
    withdrawal: str | None = None
    deposit: str | None = None
    balance: str
    reference: str | None = None
    check_number: str | None = None


class StatementResponse(BaseModel):
    """Parsed bank statement."""

    account_number: str
    account_name: str | None = None
    statement_period_start: dt.date
    statement_period_end: dt.date
    opening_balance: str
    closing_balance: str
    transactions: list[TransactionResponse]
    source_pdf: str
    language: str
    bank: str
    branch: str | None = None
    currency: str = "THB"


class AccountResponse(BaseModel):
    """Consolidated account with deduplicated transactions."""

    account_number: str
    account_name: str | None = None
    statement_count: int
    all_transactions: list[TransactionResponse]
    transaction_count: int


class ParseResponse(BaseModel):
    """Response from parsing PDFs."""

    statements: list[StatementResponse]
    errors: list[dict]


class ConsolidateRequest(BaseModel):
    """Request to consolidate statements."""

    statements: list[StatementResponse]
    preferred_language: str = "en"


class ConsolidateResponse(BaseModel):
    """Response from consolidation."""

    accounts: list[AccountResponse]
    account_count: int


class ValidateRequest(BaseModel):
    """Request to validate balance continuity."""

    statements: list[StatementResponse]


class BalanceIssue(BaseModel):
    """A balance continuity issue."""

    account_number: str
    statement_file: str
    expected_opening: str
    actual_opening: str
    previous_statement_file: str | None = None


class ValidateResponse(BaseModel):
    """Response from validation."""

    is_valid: bool
    issues: list[BalanceIssue]


class ExportRequest(BaseModel):
    """Request to export statements."""

    statements: list[StatementResponse]
    preferred_language: str = "en"
