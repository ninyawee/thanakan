# thanakan-mail

Download Thai bank PDF statements from email (Gmail).

## Features

- OAuth 2.0 authentication with Gmail API
- Download PDF statement attachments from KBank, BBL, and SCB emails
- Filter by bank-specific sender addresses and filename patterns
- Extensible provider architecture for future email services

## Environment Variables

- `GMAIL_CLIENT_SECRET`: Path to Google OAuth client_secret.json (required)
- `GMAIL_TOKEN_PATH`: Path to store OAuth token (default: ~/.thanakan/gmail_token.json)

## CLI Usage

```bash
# Authenticate with Gmail
thanakan mail auth

# Download statements from a specific bank
thanakan mail download kbank
thanakan mail download bbl --output ./statements
thanakan mail download scb --max 50

# Download from all supported banks
thanakan mail download all

# Download and parse PDFs in one step
thanakan mail download kbank --parse
```

## Library Usage

```python
from thanakan_mail import GmailProvider, StatementDownloader, BANK_CONFIGS

# Initialize provider and downloader
provider = GmailProvider()
downloader = StatementDownloader(provider, BANK_CONFIGS["kbank"], "./downloads")

# Download statements
results = downloader.download_statements(max_emails=100, verbose=True)

# Check results
for result in results:
    print(f"Email: {result.message.subject}")
    print(f"  Downloaded: {result.downloaded_files}")
    print(f"  Skipped: {result.skipped_attachments}")
    print(f"  Errors: {result.errors}")
```

## Setup

1. Create a Google Cloud project and enable the Gmail API
2. Create OAuth 2.0 credentials (Desktop application)
3. Download the client_secret.json file
4. Set the `GMAIL_CLIENT_SECRET` environment variable to the file path
5. Run `thanakan mail auth` to complete OAuth flow
