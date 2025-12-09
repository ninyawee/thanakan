# thanakan-statement

Thai bank PDF statement parser for KBank, BBL, and SCB.

## Installation

```bash
pip install thanakan-statement
```

## Usage

### Parse single PDF

```python
from thanakan_statement import parse_pdf

statement = parse_pdf("statement.pdf", password="DDMMYYYY")

print(f"Account: {statement.account_number}")
print(f"Bank: {statement.bank}")
print(f"Transactions: {len(statement.transactions)}")
```

### Parse directory

```python
from thanakan_statement import parse_all_pdfs

statements = parse_all_pdfs("./statements/", password="DDMMYYYY")
```

### Consolidate by account

```python
from thanakan_statement import parse_all_pdfs, consolidate_by_account

statements = parse_all_pdfs("./statements/")
accounts = consolidate_by_account(statements, preferred_language="en")

for account in accounts:
    print(f"{account.account_number}: {len(account.all_transactions)} transactions")
```

### Export

```python
from thanakan_statement import (
    parse_all_pdfs,
    consolidate_by_account,
    export_to_json,
    export_to_csv,
    export_to_excel,
)

statements = parse_all_pdfs("./statements/")
accounts = consolidate_by_account(statements)

# Export to JSON
export_to_json(accounts, "output.json")

# Export to CSV (one file per account)
export_to_csv(accounts, "./csv_output/")

# Export to Excel (one sheet per account)
export_to_excel(accounts, "output.xlsx")
```

### Validate balance continuity

```python
from thanakan_statement import parse_all_pdfs, validate_balance_continuity

statements = parse_all_pdfs("./statements/")
statements.sort(key=lambda s: s.statement_period_start)

is_valid, issues = validate_balance_continuity(statements)
if not is_valid:
    for issue in issues:
        print(f"Issue in {issue.statement.source_pdf}")
```

## Supported Banks

| Bank | Statement Format | Languages |
|------|-----------------|-----------|
| KBank | PDF | Thai, English |
| BBL | PDF | Thai, English |
| SCB | PDF | Thai, English |

## PDF Password

Most bank statement PDFs are password-protected with birthdate (DDMMYYYY):

```python
# Specify directly
statement = parse_pdf("statement.pdf", password="02011995")

# Or use environment variable
import os
os.environ["PDF_PASS"] = "02011995"
statement = parse_pdf("statement.pdf")
```

## Documentation

Full documentation: https://ninyawee.github.io/thanakan/libraries/thanakan-statement/
