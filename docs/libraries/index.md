# Libraries

Thanakan ประกอบด้วย 5 library ที่สามารถใช้งานแยกกันได้:

| Library | คำอธิบาย |
|---------|----------|
| [thanakan-qr](thanakan-qr.md) | อ่าน QR Code จากสลิปโอนเงิน |
| [thanakan-oauth](thanakan-oauth.md) | API clients สำหรับ SCB และ KBank |
| [thanakan-statement](thanakan-statement.md) | อ่าน PDF Statement (KBank, BBL) |
| [thanakan-mail](thanakan-mail.md) | ดาวน์โหลด Statement จาก Gmail |
| [thanakan-accounting](thanakan-accounting.md) | ส่งออกไปยังโปรแกรมบัญชี |

## การติดตั้ง

### ติดตั้งทั้งหมด

```bash
pip install thanakan
```

### ติดตั้งแยก

```bash
pip install thanakan-qr
pip install thanakan-oauth
pip install thanakan-statement
pip install thanakan-mail
pip install thanakan-accounting
```

## การ Import

### จาก package หลัก

```python
from thanakan import (
    # QR
    SlipQRData,
    QrPayload,

    # OAuth
    SCBAPI,
    KBankAPI,
    SCBBaseURL,
)
```

### จาก package ย่อย

```python
from thanakan_qr import SlipQRData, QrPayload
from thanakan_oauth import SCBAPI, KBankAPI
from thanakan_statement import parse_pdf, Statement, Transaction
from thanakan_mail import GmailProvider, StatementDownloader
from thanakan_accounting import export_to_peak
```

## ตัวอย่าง Workflow

### อ่าน QR และตรวจสอบสลิป

```python
from PIL import Image
from thanakan import SlipQRData, SCBAPI

# 1. อ่าน QR จากสลิป
image = Image.open("slip.png")
qr_data = SlipQRData.create_from_image(image)

# 2. ตรวจสอบกับ SCB API
api = SCBAPI(
    app_key="your_app_key",
    app_secret="your_app_secret",
    cert="/path/to/cert.pem"
)

result = await api.verify_slip(
    qr_data.payload.sending_bank_id,
    qr_data.payload.transaction_ref_id
)

print(f"จำนวนเงิน: {result.data.amount}")
print(f"ผู้โอน: {result.data.sender.name}")
```

### ดาวน์โหลดและ Parse Statement

```python
from thanakan_mail import GmailProvider, StatementDownloader, BANK_CONFIGS
from thanakan_statement import parse_all_pdfs, consolidate_by_account

# 1. ดาวน์โหลดจาก Gmail
provider = GmailProvider()
downloader = StatementDownloader(provider, BANK_CONFIGS["kbank"], "./downloads")
downloader.download_statements(max_emails=100)

# 2. Parse PDF
statements = parse_all_pdfs("./downloads")
accounts = consolidate_by_account(statements)

# 3. ดูข้อมูล
for account in accounts:
    print(f"บัญชี: {account.account_number}")
    print(f"รายการ: {len(account.all_transactions)}")
```

### Export ไปยัง Peak

```python
from thanakan_statement import parse_all_pdfs, consolidate_by_account
from thanakan_accounting import export_to_peak

# Parse และ consolidate
statements = parse_all_pdfs("./statements")
accounts = consolidate_by_account(statements)

# Export
export_to_peak(accounts, "peak_import.xlsx")
```
