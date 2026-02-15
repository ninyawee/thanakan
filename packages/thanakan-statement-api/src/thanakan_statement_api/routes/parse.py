"""Parse routes for uploading and parsing PDF statements."""

import os
import tempfile
from datetime import date, time
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from thanakan_statement import (
    Statement,
    Transaction,
    parse_pdf,
    consolidate_by_account,
    validate_balance_continuity,
)
from thanakan_statement.consolidate import group_statements_by_account

from ..models import (
    ParseResponse,
    ConsolidateRequest,
    ConsolidateResponse,
    ValidateRequest,
    ValidateResponse,
    BalanceIssue,
    StatementResponse,
)
from ..utils.serializers import statement_to_response, account_to_response

router = APIRouter()


def response_to_statement(resp: StatementResponse) -> Statement:
    """Convert StatementResponse back to Statement model for library functions."""
    transactions = [
        Transaction(
            date=t.date,
            time=t.time,
            description=t.description,
            channel=t.channel,
            withdrawal=Decimal(t.withdrawal) if t.withdrawal else None,
            deposit=Decimal(t.deposit) if t.deposit else None,
            balance=Decimal(t.balance),
            reference=t.reference,
            check_number=t.check_number,
        )
        for t in resp.transactions
    ]
    return Statement(
        account_number=resp.account_number,
        account_name=resp.account_name,
        statement_period_start=resp.statement_period_start,
        statement_period_end=resp.statement_period_end,
        opening_balance=Decimal(resp.opening_balance),
        closing_balance=Decimal(resp.closing_balance),
        transactions=transactions,
        source_pdf=resp.source_pdf,
        language=resp.language,
        bank=resp.bank,
        branch=resp.branch,
        currency=resp.currency,
    )


@router.post("/parse", response_model=ParseResponse)
async def parse_statements(
    files: list[UploadFile] = File(...),
    password: str | None = Form(None),
):
    """Upload and parse PDF statements.

    Args:
        files: PDF files to parse
        password: Optional PDF password (DDMMYYYY format for Thai bank statements)

    Returns:
        Parsed statements and any errors encountered
    """
    # Use PDF_PASS from environment if no password provided
    pdf_password = password or os.environ.get("PDF_PASS")

    statements: list[StatementResponse] = []
    errors: list[dict] = []

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            errors.append({"filename": file.filename or "unknown", "error": "Not a PDF file"})
            continue

        # Write to temp file for parsing
        try:
            content = await file.read()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            try:
                stmt = parse_pdf(tmp_path, password=pdf_password)
                # Override source_pdf with original filename
                stmt.source_pdf = file.filename
                statements.append(statement_to_response(stmt))
            except Exception as e:
                errors.append({"filename": file.filename, "error": str(e)})
            finally:
                tmp_path.unlink(missing_ok=True)
        except Exception as e:
            errors.append({"filename": file.filename or "unknown", "error": str(e)})

    return ParseResponse(statements=statements, errors=errors)


@router.post("/consolidate", response_model=ConsolidateResponse)
async def consolidate_statements(request: ConsolidateRequest):
    """Consolidate statements by account.

    Groups statements by account number, deduplicates transactions,
    and prefers the specified language when statements overlap.

    Args:
        request: Statements to consolidate and preferred language

    Returns:
        Consolidated accounts
    """
    # Convert responses back to Statement objects
    statements = [response_to_statement(s) for s in request.statements]

    # Consolidate using library function
    accounts = consolidate_by_account(statements, request.preferred_language)

    return ConsolidateResponse(
        accounts=[account_to_response(acc) for acc in accounts],
        account_count=len(accounts),
    )


@router.post("/validate", response_model=ValidateResponse)
async def validate_statements(request: ValidateRequest):
    """Validate balance continuity across statements.

    Checks that each statement's opening balance matches the
    previous statement's closing balance for consecutive periods.

    Args:
        request: Statements to validate

    Returns:
        Validation result with any issues found
    """
    # Convert responses back to Statement objects
    statements = [response_to_statement(s) for s in request.statements]

    # Group by account and validate each
    groups = group_statements_by_account(statements)
    all_issues: list[BalanceIssue] = []

    for account_number, account_statements in groups.items():
        # Sort by period start for validation
        account_statements.sort(key=lambda s: s.statement_period_start)

        is_valid, issues = validate_balance_continuity(account_statements)

        for issue in issues:
            all_issues.append(
                BalanceIssue(
                    account_number=account_number,
                    statement_file=issue.statement.source_pdf,
                    expected_opening=str(issue.expected_opening),
                    actual_opening=str(issue.actual_opening),
                    previous_statement_file=(
                        issue.prev_statement.source_pdf if issue.prev_statement else None
                    ),
                )
            )

    return ValidateResponse(
        is_valid=len(all_issues) == 0,
        issues=all_issues,
    )
