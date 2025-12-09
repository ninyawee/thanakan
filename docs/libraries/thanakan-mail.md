# thanakan-mail

ดาวน์โหลด Statement PDF จาก Gmail

## การติดตั้ง

```bash
pip install thanakan-mail
```

## Quick Start

```python
from thanakan_mail import GmailProvider, StatementDownloader, BANK_CONFIGS

# ยืนยันตัวตน (ครั้งแรก)
provider = GmailProvider(client_secret_path="./client_secret.json")
provider.authenticate()

# ดาวน์โหลด Statement
downloader = StatementDownloader(provider, BANK_CONFIGS["kbank"], "./downloads")
results = downloader.download_statements(max_emails=100)
```

---

## การตั้งค่า Gmail API

### 1. สร้าง Google Cloud Project

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้าง Project ใหม่
3. ไปที่ **APIs & Services** > **Enable APIs**
4. ค้นหาและเปิดใช้งาน **Gmail API**

### 2. สร้าง OAuth Credentials

1. ไปที่ **APIs & Services** > **Credentials**
2. คลิก **Create Credentials** > **OAuth client ID**
3. เลือก **Desktop application**
4. ดาวน์โหลด JSON file (client_secret.json)

### 3. ตั้งค่า Environment Variables

```bash
export GMAIL_CLIENT_SECRET=/path/to/client_secret.json
export GMAIL_TOKEN_PATH=~/.thanakan/gmail_token.json  # optional
```

---

## GmailProvider

Provider สำหรับเชื่อมต่อ Gmail API

### Constructor

```python
GmailProvider(
    client_secret_path: str | Path | None = None,
    token_path: str | Path | None = None
)
```

| Parameter | Default | คำอธิบาย |
|-----------|---------|----------|
| `client_secret_path` | env `GMAIL_CLIENT_SECRET` | Path ไปยัง client_secret.json |
| `token_path` | `~/.thanakan/gmail_token.json` | Path สำหรับเก็บ OAuth token |

### Methods

#### authenticate

ยืนยันตัวตนกับ Gmail (เปิด browser)

```python
provider = GmailProvider()
provider.authenticate()
```

#### get_profile

ดึงข้อมูล Gmail profile

```python
profile = provider.get_profile()
print(f"Email: {profile['emailAddress']}")
print(f"Messages: {profile['messagesTotal']}")
```

---

## StatementDownloader

ดาวน์โหลด Statement PDF จาก email

### Constructor

```python
StatementDownloader(
    provider: EmailProvider,
    bank_config: BankEmailConfig,
    output_dir: str | Path
)
```

| Parameter | คำอธิบาย |
|-----------|----------|
| `provider` | Email provider (เช่น `GmailProvider`) |
| `bank_config` | Configuration ของธนาคาร |
| `output_dir` | Directory สำหรับบันทึก PDF |

### Methods

#### download_statements

ดาวน์โหลด Statement จาก email

```python
results = downloader.download_statements(
    max_emails=100,
    verbose=True
)

for result in results:
    print(f"Email: {result.message.subject}")
    print(f"Downloaded: {result.downloaded_files}")
```

**Returns:** `list[DownloadResult]`

---

## Bank Configurations

### BANK_CONFIGS

Dictionary ของ configuration ทุกธนาคาร

```python
from thanakan_mail import BANK_CONFIGS

kbank_config = BANK_CONFIGS["kbank"]
bbl_config = BANK_CONFIGS["bbl"]
scb_config = BANK_CONFIGS["scb"]
```

### Individual Configs

```python
from thanakan_mail import KBANK_CONFIG, BBL_CONFIG, SCB_CONFIG
```

| Config | Sender Email |
|--------|--------------|
| `KBANK_CONFIG` | `no-reply@kasikornbank.com` |
| `BBL_CONFIG` | `estatement@bangkokbank.com` |
| `SCB_CONFIG` | `scbestatement@scb.co.th` |

---

## Models

### DownloadResult

ผลการดาวน์โหลดจาก email

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `message` | `EmailMessage` | ข้อมูล email |
| `downloaded_files` | `list[str]` | ไฟล์ที่ดาวน์โหลดสำเร็จ |
| `skipped_attachments` | `list[str]` | ไฟล์ที่ข้าม |
| `errors` | `list[str]` | Error messages |

### EmailMessage

ข้อมูล email

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `message_id` | `str` | ID ของ email |
| `subject` | `str` | หัวข้อ |
| `date` | `datetime` | วันที่ |
| `sender` | `str` | ผู้ส่ง |
| `attachments` | `list[EmailAttachment]` | Attachments |

---

## PDF Unlock Utilities

### unlock_pdf

ปลดล็อค PDF ที่มีรหัสผ่าน

```python
from thanakan_mail import unlock_pdf

unlock_pdf(
    input_path="encrypted.pdf",
    output_path="decrypted.pdf",
    password="DDMMYYYY"
)
```

### unlock_pdfs

ปลดล็อค PDF หลายไฟล์

```python
from thanakan_mail import unlock_pdfs

unlock_pdfs(
    directory="./encrypted/",
    output_dir="./decrypted/",
    password="DDMMYYYY"
)
```

### is_pdf_encrypted

ตรวจสอบว่า PDF มีรหัสผ่านหรือไม่

```python
from thanakan_mail import is_pdf_encrypted

if is_pdf_encrypted("statement.pdf"):
    print("PDF มีรหัสผ่าน")
```

---

## Metadata

### save_metadata

บันทึก metadata เป็น JSON

```python
from thanakan_mail import save_metadata

save_metadata(results, "metadata.json")
```

### results_to_metadata

แปลง results เป็น metadata list

```python
from thanakan_mail import results_to_metadata

metadata = results_to_metadata(results)
```

---

## ตัวอย่างการใช้งาน

### ดาวน์โหลดจากทุกธนาคาร

```python
from thanakan_mail import GmailProvider, StatementDownloader, BANK_CONFIGS

provider = GmailProvider()

for bank_name, bank_config in BANK_CONFIGS.items():
    print(f"Downloading from {bank_name}...")
    downloader = StatementDownloader(provider, bank_config, f"./downloads/{bank_name}")
    results = downloader.download_statements(max_emails=50)
    print(f"  Downloaded {sum(len(r.downloaded_files) for r in results)} PDFs")
```

### ดาวน์โหลดและ Parse

```python
from thanakan_mail import GmailProvider, StatementDownloader, BANK_CONFIGS
from thanakan_statement import parse_all_pdfs, consolidate_by_account

# ดาวน์โหลด
provider = GmailProvider()
downloader = StatementDownloader(provider, BANK_CONFIGS["kbank"], "./downloads")
downloader.download_statements()

# Parse
statements = parse_all_pdfs("./downloads")
accounts = consolidate_by_account(statements)

for account in accounts:
    print(f"{account.account_number}: {len(account.all_transactions)} transactions")
```
