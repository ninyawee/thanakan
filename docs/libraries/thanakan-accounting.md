# thanakan-accounting

ส่งออก Statement ไปยังโปรแกรมบัญชี

## การติดตั้ง

```bash
pip install thanakan-accounting
```

## Quick Start

```python
from thanakan_statement import parse_all_pdfs, consolidate_by_account
from thanakan_accounting import export_to_peak

# Parse statements
statements = parse_all_pdfs("./statements/")
accounts = consolidate_by_account(statements)

# Export to Peak format
export_to_peak(accounts, "peak_import.xlsx")
```

---

## รูปแบบที่รองรับ

| โปรแกรม | Function | คำอธิบาย |
|---------|----------|----------|
| Peak | `export_to_peak` | Peak Import Statement format |

---

## Peak Export

### export_to_peak

Export หลายบัญชีเป็น Excel file (แยก sheet ต่อบัญชี)

```python
from thanakan_accounting import export_to_peak

export_to_peak(accounts, "peak_import.xlsx")
```

**Parameters:**

| Parameter | Type | คำอธิบาย |
|-----------|------|----------|
| `accounts` | `list[Account]` | บัญชีที่จะ export |
| `output_path` | `str \| Path` | Path สำหรับ output Excel file |

### export_single_to_peak

Export บัญชีเดียว

```python
from thanakan_accounting import export_single_to_peak

export_single_to_peak(accounts[0], "peak_single.xlsx")
```

---

## รูปแบบ Peak Import Statement

ไฟล์ Excel ที่สร้างมีรูปแบบตาม Peak Import Statement:

| Column | ชื่อ | รูปแบบ | ตัวอย่าง |
|--------|------|--------|----------|
| A | วันที่รายการ | YYYYMMDD | `20240115` |
| B | จำนวนเงิน | Number | `-1500.00`, `3000.00` |
| C | หมายเหตุ | Text | `โอนเงิน K PLUS - REF123` |

### ตัวอย่าง Output

| วันที่รายการ | จำนวนเงิน | หมายเหตุ |
|-------------|-----------|----------|
| 20240115 | -1500.00 | โอนเงิน K PLUS - REF123456 |
| 20240116 | 3000.00 | เงินเข้า - Transfer from BBL |
| 20240117 | -500.00 | PromptPay - 0812345678 |

### หมายเหตุ

- **ถอนเงิน**: จำนวนเป็นลบ (-)
- **ฝากเงิน**: จำนวนเป็นบวก (+)
- **หมายเหตุ**: รวมจาก description + channel + check number + reference

---

## ตัวอย่างการใช้งาน

### Full Pipeline

```python
from thanakan_statement import parse_all_pdfs, consolidate_by_account
from thanakan_accounting import export_to_peak

# 1. Parse PDF statements
statements = parse_all_pdfs("./statements/", password="DDMMYYYY")

# 2. Consolidate by account (remove duplicates)
accounts = consolidate_by_account(statements, preferred_language="en")

# 3. Export to Peak format
export_to_peak(accounts, "peak_import.xlsx")

print(f"Exported {len(accounts)} accounts")
for account in accounts:
    print(f"  {account.account_number}: {len(account.all_transactions)} transactions")
```

### With Gmail Download

```python
from thanakan_mail import GmailProvider, StatementDownloader, BANK_CONFIGS
from thanakan_statement import parse_all_pdfs, consolidate_by_account
from thanakan_accounting import export_to_peak

# 1. Download from Gmail
provider = GmailProvider()
downloader = StatementDownloader(provider, BANK_CONFIGS["kbank"], "./downloads")
downloader.download_statements(max_emails=100)

# 2. Parse
statements = parse_all_pdfs("./downloads")
accounts = consolidate_by_account(statements)

# 3. Export
export_to_peak(accounts, "peak_import.xlsx")
```

---

## เพิ่ม Exporter ใหม่

สามารถเพิ่ม exporter สำหรับโปรแกรมบัญชีอื่นได้:

```python
# exporters/zoho.py
from pathlib import Path
from thanakan_statement import Account

def export_to_zoho(accounts: list[Account], output_path: Path | str) -> None:
    """Export to Zoho Books format."""
    # Implementation here
    pass
```

แล้วเพิ่มใน `__init__.py`:

```python
from .exporters.zoho import export_to_zoho

__all__ = [
    "export_to_peak",
    "export_single_to_peak",
    "export_to_zoho",
]
```

---

## การ Import เข้า Peak

1. เปิด Peak และไปที่ **Bank Statement**
2. เลือกบัญชีธนาคารที่ต้องการ
3. คลิก **Import Statement**
4. เลือกไฟล์ Excel ที่ export
5. ตรวจสอบข้อมูลและยืนยันการ import
6. ทำ Bank Reconciliation ตามปกติ
