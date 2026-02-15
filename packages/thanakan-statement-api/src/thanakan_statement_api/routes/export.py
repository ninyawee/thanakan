"""Export routes for downloading statements in various formats."""

import io
import tempfile
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from thanakan_statement import (
    Account,
    Statement,
    Transaction,
    consolidate_by_account,
    export_to_json,
    export_to_csv,
    export_to_excel,
)

from ..models import ExportRequest, StatementResponse

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


def get_accounts_from_request(request: ExportRequest) -> list[Account]:
    """Convert request statements to consolidated accounts."""
    statements = [response_to_statement(s) for s in request.statements]
    return consolidate_by_account(statements, request.preferred_language)


@router.post("/export/json")
async def export_json(request: ExportRequest):
    """Export statements to JSON file download."""
    accounts = get_accounts_from_request(request)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        export_to_json(accounts, tmp_path)
        content = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)

    filename = f"statements_{date.today().isoformat()}.json"

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/csv")
async def export_csv(request: ExportRequest):
    """Export statements to ZIP of CSV files (one per account)."""
    accounts = get_accounts_from_request(request)

    with tempfile.TemporaryDirectory() as tmpdir:
        export_to_csv(accounts, Path(tmpdir))

        # Create zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for csv_file in Path(tmpdir).glob("*.csv"):
                zf.write(csv_file, csv_file.name)

        zip_buffer.seek(0)

    filename = f"statements_{date.today().isoformat()}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/excel")
async def export_excel(request: ExportRequest):
    """Export statements to Excel file download."""
    accounts = get_accounts_from_request(request)

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        export_to_excel(accounts, tmp_path)
        content = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)

    filename = f"statements_{date.today().isoformat()}.xlsx"

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
