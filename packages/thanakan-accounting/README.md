# thanakan-accounting

Export Thai bank statements to accounting software formats.

## Supported Formats

- **Peak Import Statement** - Excel format for [Peak](https://www.peakaccount.com/) reconciliation

## Usage

```python
from thanakan_statement import parse_all_pdfs, consolidate_by_account
from thanakan_accounting import export_to_peak, export_single_to_peak

# Parse bank statements
statements = parse_all_pdfs("./statements/")
accounts = consolidate_by_account(statements)

# Export all accounts to Peak format (one sheet per account)
export_to_peak(accounts, "peak_import.xlsx")

# Or export a single account
export_single_to_peak(accounts[0], "peak_import_single.xlsx")
```

## Peak Import Format

The Peak exporter generates Excel files with 3 columns:

| Column | Name | Format |
|--------|------|--------|
| A | วันที่รายการ | YYYYMMDD |
| B | จำนวนเงิน | Number (- for withdrawal, + for deposit) |
| C | หมายเหตุ | Description + Channel + Check# + Reference |

## Adding New Exporters

Add new exporters in `exporters/` directory following the same pattern:

```python
# exporters/zoho.py
from pathlib import Path
from thanakan_statement import Account

def export_to_zoho(accounts: list[Account], output_path: Path | str) -> None:
    ...
```
