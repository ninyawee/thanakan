# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

This is a Python monorepo using [uv](https://github.com/astral-sh/uv) for package management. Python version is managed by mise (3.14.2).

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_qr_data.py

# Run a specific test function
uv run pytest tests/test_qr_data.py::test_function_name
```

## Architecture

**thanakan** is a Thai bank utilities monorepo with three workspace packages:

### thanakan-qr (`packages/thanakan-qr`)
Parses Thai bank slip mini QR codes following the SCB specification. Extracts transaction reference ID and sending bank ID from QR data on payment slips.

Key exports: `SlipQRData`, `QrPayload`, `not_bank_slip`, `expect_single_qrcode`

Entry point: `SlipQRData.create_from_image(pil_image)` or `SlipQRData.create_from_code(code_string)`

### thanakan-oauth (`packages/thanakan-oauth`)
OAuth API clients for Thai banks (SCB, KBank) for slip verification and payment operations.

Key exports: `SCBAPI`, `SCBBaseURL`, `KBankAPI`

Both bank clients use custom OAuth2 implementations extending `httpx-auth` because the banks have non-standard OAuth flows. Both support async and sync operations (via `client` and `client_sync` respectively).

**SCBAPI** features:
- QR30 code generation (`create_qr30`)
- Slip verification (`verify_slip`)
- Transaction inquiry (`query_transaction`)
- Deeplink creation/retrieval (`create_deeplink`, `get_deeplink`)

**KBankAPI** features:
- Slip verification (`verify_slip`, `verify_slip_sync`)

Both APIs require mTLS certificates for production use.

### thanakan-statement (`packages/thanakan-statement`)
Parses Thai bank PDF statements (KBank, BBL) and extracts transaction data. Supports password-protected PDFs, bilingual statements (Thai/English), and consolidation of multiple statements.

Key exports: `Transaction`, `Statement`, `Account`, `parse_pdf`, `parse_all_pdfs`, `consolidate_by_account`, `export_to_json`, `export_to_csv`, `export_to_excel`

**Parsing**:
- `parse_pdf(pdf_path, password)` - Parse a single PDF, returns `Statement`
- `parse_all_pdfs(directory, password)` - Parse all PDFs in a directory, returns `list[Statement]`
- Auto-detects bank type (KBank vs BBL) and language (Thai vs English)
- Default PDF password from `PDF_PASS` env var or `"DDMMYYYY"`

**Consolidation**:
- `consolidate_by_account(statements, preferred_language)` - Groups by account, deduplicates transactions, returns `list[Account]`
- `validate_balance_continuity(statements)` - Validates balance flow between statements

**Export**:
- `export_to_json(accounts, path)` - Full structured JSON
- `export_to_csv(accounts, directory)` - One CSV per account
- `export_to_excel(accounts, path)` - One sheet per account

### CLI (`src/thanakan/cli*.py`)
Command-line interface built with Typer. Entry point is `thanakan`.

**Commands:**
- `thanakan qr` - Parse QR from image, raw string, or stdin
- `thanakan statement parse` - Parse PDF statements to JSON
- `thanakan statement export` - Parse and export to JSON/CSV/Excel
- `thanakan mail download` - Download statements from Gmail
- `thanakan accounting peak` - Export to Peak accounting format

**Pipe-friendly design (qr command):**
- Reads from stdin when piped (auto-detects text vs image via magic bytes)
- Outputs compact JSON when piped, pretty JSON in terminal
- Example: `echo "QR_DATA" | thanakan qr | jq .payload`

### Models
Pydantic models use camelCase aliasing (`APIModel` base class) to match bank API JSON conventions. `SlipData` is the common response structure for slip verification across both banks.
