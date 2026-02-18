"""Serialization utilities for converting between library models and API responses."""

from thanakan_statement import Statement, Transaction, Account

from ..models import StatementResponse, TransactionResponse, AccountResponse


def transaction_to_response(txn: Transaction) -> TransactionResponse:
    """Convert Transaction model to JSON-serializable response."""
    return TransactionResponse(
        date=txn.date,
        time=txn.time,
        description=txn.description,
        channel=txn.channel,
        withdrawal=str(txn.withdrawal) if txn.withdrawal is not None else None,
        deposit=str(txn.deposit) if txn.deposit is not None else None,
        balance=str(txn.balance),
        reference=txn.reference,
        check_number=txn.check_number,
    )


def statement_to_response(stmt: Statement) -> StatementResponse:
    """Convert Statement model to JSON-serializable response."""
    return StatementResponse(
        account_number=stmt.account_number,
        account_name=stmt.account_name,
        statement_period_start=stmt.statement_period_start,
        statement_period_end=stmt.statement_period_end,
        opening_balance=str(stmt.opening_balance),
        closing_balance=str(stmt.closing_balance),
        transactions=[transaction_to_response(t) for t in stmt.transactions],
        source_pdf=stmt.source_pdf,
        language=stmt.language,
        bank=stmt.bank,
        branch=stmt.branch,
        currency=stmt.currency,
    )


def account_to_response(acc: Account) -> AccountResponse:
    """Convert Account model to JSON-serializable response."""
    return AccountResponse(
        account_number=acc.account_number,
        account_name=acc.account_name,
        statement_count=len(acc.statements),
        all_transactions=[transaction_to_response(t) for t in acc.all_transactions],
        transaction_count=len(acc.all_transactions),
    )
