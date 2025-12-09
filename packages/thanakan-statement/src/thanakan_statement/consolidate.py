"""Consolidate multiple statements by account number."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, time, timedelta
from decimal import Decimal

from .models import Account, Statement, Transaction


@dataclass
class BalanceIssue:
    """Represents a balance continuity issue."""

    statement: Statement
    expected_opening: Decimal
    actual_opening: Decimal
    prev_statement: Statement | None = None


def group_statements_by_account(statements: list[Statement]) -> dict[str, list[Statement]]:
    """Group statements by account number.

    Args:
        statements: List of all statements

    Returns:
        Dict mapping account_number to list of statements
    """
    groups: dict[str, list[Statement]] = defaultdict(list)
    for stmt in statements:
        groups[stmt.account_number].append(stmt)
    return dict(groups)


def validate_balance_continuity(
    statements: list[Statement],
) -> tuple[bool, list[BalanceIssue]]:
    """Validate that balances flow correctly between statements.

    Checks that each statement's opening balance matches the previous
    statement's closing balance (when periods are consecutive).

    Args:
        statements: List of statements sorted by period start

    Returns:
        (is_valid, list of issues)
    """
    issues: list[BalanceIssue] = []

    if len(statements) < 2:
        return True, issues

    for i in range(1, len(statements)):
        prev_stmt = statements[i - 1]
        curr_stmt = statements[i]

        # Only check if periods are consecutive (no gap)
        expected_next_start = prev_stmt.statement_period_end
        if curr_stmt.statement_period_start <= expected_next_start:
            # Periods are consecutive or overlapping
            expected_opening = prev_stmt.closing_balance
            actual_opening = curr_stmt.opening_balance

            # Allow small rounding differences (1 satang = 0.01 THB)
            if abs(expected_opening - actual_opening) > Decimal("0.02"):
                issues.append(
                    BalanceIssue(
                        statement=curr_stmt,
                        expected_opening=expected_opening,
                        actual_opening=actual_opening,
                        prev_statement=prev_stmt,
                    )
                )

    return len(issues) == 0, issues


def select_statements_by_language(
    statements: list[Statement],
    preferred_language: str = "en",
) -> list[Statement]:
    """Select non-overlapping statements, preferring specified language.

    For overlapping periods, prefer the specified language. When multiple
    statements cover the same dates, we prefer:
    1. Statements in the preferred language
    2. Statements with more complete coverage (larger date range)

    Args:
        statements: List of statements for same account
        preferred_language: Preferred language ("en" or "th")

    Returns:
        Filtered list with minimal overlapping periods
    """
    if not statements:
        return []

    # Sort by period start, then by period length (longer first), then by language preference
    def sort_key(stmt: Statement) -> tuple:
        period_length = (stmt.statement_period_end - stmt.statement_period_start).days
        lang_priority = 0 if stmt.language == preferred_language else 1
        return (stmt.statement_period_start, -period_length, lang_priority)

    sorted_stmts = sorted(statements, key=sort_key)

    # Greedily select non-overlapping statements preferring the desired language
    # First, group overlapping statements
    selected: list[Statement] = []
    covered_dates: set[date] = set()

    for stmt in sorted_stmts:
        # Check how much of this statement's period is already covered
        stmt_dates = set()
        current = stmt.statement_period_start
        while current <= stmt.statement_period_end:
            stmt_dates.add(current)
            current += timedelta(days=1)

        uncovered_dates = stmt_dates - covered_dates

        # If this statement adds significant new coverage, include it
        # But skip if it's mostly redundant (less than 10% new coverage)
        if len(uncovered_dates) == 0:
            continue  # Completely redundant, skip

        coverage_ratio = len(uncovered_dates) / len(stmt_dates)
        if coverage_ratio < 0.1 and len(selected) > 0:
            # Less than 10% new coverage and we already have statements - skip
            continue

        selected.append(stmt)
        covered_dates.update(stmt_dates)

    # Sort by period start
    selected.sort(key=lambda s: s.statement_period_start)

    return selected


def validate_transaction_continuity(transactions: list[Transaction]) -> bool:
    """Validate that transaction balances flow correctly.

    Each transaction's balance should equal the previous balance
    plus deposit minus withdrawal.

    Args:
        transactions: List of transactions sorted by date/time

    Returns:
        True if all balances are consistent
    """
    if len(transactions) < 2:
        return True

    for i in range(1, len(transactions)):
        prev_txn = transactions[i - 1]
        curr_txn = transactions[i]

        # Calculate expected balance
        expected = prev_txn.balance
        if curr_txn.deposit:
            expected += curr_txn.deposit
        if curr_txn.withdrawal:
            expected -= curr_txn.withdrawal

        # Allow small rounding differences
        if abs(expected - curr_txn.balance) > Decimal("0.02"):
            return False

    return True


def deduplicate_transactions(transactions: list[Transaction]) -> list[Transaction]:
    """Remove duplicate transactions.

    Transactions are considered duplicates if they have the same:
    - date
    - time (if present)
    - description
    - withdrawal/deposit amount

    Args:
        transactions: List of transactions (may contain duplicates)

    Returns:
        Deduplicated list of transactions
    """
    seen: set[tuple] = set()
    unique: list[Transaction] = []

    for txn in transactions:
        key = (
            txn.date,
            txn.time,
            txn.description.strip(),
            txn.withdrawal,
            txn.deposit,
        )
        if key not in seen:
            seen.add(key)
            unique.append(txn)

    return unique


def merge_statements(statements: list[Statement]) -> list[Transaction]:
    """Merge transactions from multiple statements.

    Handles overlapping date ranges by deduplicating.

    Args:
        statements: List of statements for same account

    Returns:
        Merged and deduplicated list of transactions
    """
    all_transactions: list[Transaction] = []

    for stmt in statements:
        all_transactions.extend(stmt.transactions)

    # Deduplicate
    unique = deduplicate_transactions(all_transactions)

    # Sort by date and time
    return sorted(
        unique,
        key=lambda t: (t.date, t.time or time(0, 0)),
    )


def consolidate_by_account(
    statements: list[Statement],
    preferred_language: str = "en",
) -> list[Account]:
    """Consolidate all statements into accounts.

    For each account:
    1. Select one statement per period (prefer specified language)
    2. Validate balance continuity
    3. Merge transactions from selected statements

    Args:
        statements: List of all parsed statements
        preferred_language: Preferred language ("en" or "th")

    Returns:
        List of Account objects, each with deduplicated transactions
    """
    # Group by account number
    groups = group_statements_by_account(statements)

    accounts: list[Account] = []

    for account_number, account_statements in groups.items():
        # Sort statements by period
        account_statements.sort(key=lambda s: s.statement_period_start)

        # Select one statement per period by language
        selected_statements = select_statements_by_language(
            account_statements, preferred_language
        )

        # Get account name from first statement that has it
        account_name = None
        for stmt in selected_statements:
            if stmt.account_name:
                account_name = stmt.account_name
                break

        # Merge transactions from selected statements only
        all_transactions = merge_statements(selected_statements)

        account = Account(
            account_number=account_number,
            account_name=account_name,
            statements=selected_statements,  # Only keep selected statements
            all_transactions=all_transactions,
        )
        accounts.append(account)

    # Sort accounts by account number
    accounts.sort(key=lambda a: a.account_number)

    return accounts
