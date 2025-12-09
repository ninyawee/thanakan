# thanakan-statement

อ่านและแปลง PDF Statement จากธนาคาร KBank, BBL และ SCB

## การติดตั้ง

```bash
pip install thanakan-statement
```

## Quick Start

```python
from thanakan_statement import parse_pdf, parse_all_pdfs

# อ่านไฟล์เดียว
statement = parse_pdf("statement.pdf", password="DDMMYYYY")
print(f"บัญชี: {statement.account_number}")
print(f"รายการ: {len(statement.transactions)}")

# อ่านทั้ง directory
statements = parse_all_pdfs("./statements/", password="DDMMYYYY")
```

---

## Parsing

### parse_pdf

อ่าน Statement PDF ไฟล์เดียว

```python
from thanakan_statement import parse_pdf

statement = parse_pdf(
    pdf_path="statement.pdf",
    password="DDMMYYYY"  # default จาก env PDF_PASS
)
```

**Parameters:**

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pdf_path` | `str \| Path` | - | Path ไปยัง PDF file |
| `password` | `str` | env `PDF_PASS` หรือ `DDMMYYYY` | รหัสผ่าน PDF |

**Returns:** `Statement`

### parse_all_pdfs

อ่าน Statement PDF ทั้ง directory

```python
from thanakan_statement import parse_all_pdfs

statements = parse_all_pdfs(
    directory="./statements/",
    password="DDMMYYYY"
)
```

**Returns:** `list[Statement]`

---

## Consolidation

### consolidate_by_account

รวม statements หลายไฟล์ตามบัญชี และลบรายการซ้ำ

```python
from thanakan_statement import parse_all_pdfs, consolidate_by_account

statements = parse_all_pdfs("./statements/")
accounts = consolidate_by_account(
    statements,
    preferred_language="en"  # เลือก statement ภาษาอังกฤษถ้าซ้ำกัน
)

for account in accounts:
    print(f"บัญชี: {account.account_number}")
    print(f"รายการทั้งหมด: {len(account.all_transactions)}")
```

**Parameters:**

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `statements` | `list[Statement]` | - | Statement ที่จะรวม |
| `preferred_language` | `str` | `"en"` | ภาษาที่ต้องการ (`"en"` หรือ `"th"`) |

**Returns:** `list[Account]`

### validate_balance_continuity

ตรวจสอบความต่อเนื่องของยอดเงิน

```python
from thanakan_statement import parse_all_pdfs, validate_balance_continuity

statements = parse_all_pdfs("./statements/")

# เรียง statements ตามวันที่
statements.sort(key=lambda s: s.statement_period_start)

is_valid, issues = validate_balance_continuity(statements)

if not is_valid:
    for issue in issues:
        print(f"ปัญหา: {issue.statement.source_pdf}")
        print(f"  คาดหวัง: {issue.expected_opening}")
        print(f"  จริง: {issue.actual_opening}")
```

---

## Export

### export_to_json

Export เป็น JSON file

```python
from thanakan_statement import consolidate_by_account, export_to_json

accounts = consolidate_by_account(statements)
export_to_json(accounts, "output.json")
```

### export_to_csv

Export เป็น CSV files (แยกต่อบัญชี)

```python
from thanakan_statement import consolidate_by_account, export_to_csv

accounts = consolidate_by_account(statements)
export_to_csv(accounts, "./csv_output/")
# สร้าง: ./csv_output/123-4-56789-0.csv, etc.
```

### export_to_excel

Export เป็น Excel file (แยก sheet ต่อบัญชี)

```python
from thanakan_statement import consolidate_by_account, export_to_excel

accounts = consolidate_by_account(statements)
export_to_excel(accounts, "output.xlsx")
```

---

## Models

### Statement

ข้อมูล Statement จาก PDF ไฟล์เดียว

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `account_number` | `str` | เลขบัญชี |
| `account_name` | `str` | ชื่อบัญชี |
| `bank` | `str` | ธนาคาร (`kbank`, `bbl`) |
| `language` | `str` | ภาษา (`en`, `th`) |
| `statement_period_start` | `date` | วันเริ่มต้น statement |
| `statement_period_end` | `date` | วันสิ้นสุด statement |
| `opening_balance` | `Decimal` | ยอดยกมา |
| `closing_balance` | `Decimal` | ยอดยกไป |
| `transactions` | `list[Transaction]` | รายการ transactions |
| `source_pdf` | `str` | ชื่อไฟล์ PDF ต้นฉบับ |

### Transaction

รายการ transaction

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `date` | `date` | วันที่ |
| `time` | `time \| None` | เวลา (ถ้ามี) |
| `description` | `str` | คำอธิบาย |
| `channel` | `str \| None` | ช่องทาง |
| `withdrawal` | `Decimal \| None` | ยอดถอน |
| `deposit` | `Decimal \| None` | ยอดฝาก |
| `balance` | `Decimal` | ยอดคงเหลือ |
| `check_number` | `str \| None` | เลขเช็ค |
| `reference` | `str \| None` | เลขอ้างอิง |

### Account

ข้อมูลบัญชีที่รวม statements หลายไฟล์แล้ว

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `account_number` | `str` | เลขบัญชี |
| `account_name` | `str` | ชื่อบัญชี |
| `bank` | `str` | ธนาคาร |
| `statements` | `list[Statement]` | Statement ทั้งหมด |
| `all_transactions` | `list[Transaction]` | Transaction ทั้งหมด (ไม่ซ้ำ) |

---

## ธนาคารที่รองรับ

| ธนาคาร | รูปแบบ Statement | ภาษา |
|--------|-----------------|------|
| KBank | PDF | ไทย, อังกฤษ |
| BBL | PDF | ไทย, อังกฤษ |
| SCB | PDF | ไทย, อังกฤษ |

---

## รหัสผ่าน PDF

Statement PDF ส่วนใหญ่มีรหัสผ่านเป็นวันเดือนปีเกิด (DDMMYYYY):

```python
# ระบุโดยตรง
statement = parse_pdf("statement.pdf", password="02011995")

# ใช้ environment variable
import os
os.environ["PDF_PASS"] = "02011995"
statement = parse_pdf("statement.pdf")
```
