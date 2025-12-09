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

**thanakan** is a Thai bank utilities monorepo with two workspace packages:

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

### Models
Pydantic models use camelCase aliasing (`APIModel` base class) to match bank API JSON conventions. `SlipData` is the common response structure for slip verification across both banks.
