# คำสั่ง mail

ดาวน์โหลด Statement PDF จาก Gmail

## คำสั่งย่อย

| คำสั่ง | คำอธิบาย |
|--------|----------|
| `auth` | ยืนยันตัวตนกับ Gmail (OAuth flow) |
| `download` | ดาวน์โหลด Statement PDF |

---

## auth

ยืนยันตัวตนกับ Gmail ผ่าน OAuth 2.0

### การใช้งาน

```bash
thanakan mail auth [OPTIONS]
```

### Options

| Option | Short | คำอธิบาย |
|--------|-------|----------|
| `--client-secret` | `-c` | Path ไปยัง client_secret.json (หรือ env `GMAIL_CLIENT_SECRET`) |

### ตัวอย่าง

```bash
# ใช้ path จาก environment variable
thanakan mail auth

# ระบุ path โดยตรง
thanakan mail auth --client-secret ./client_secret.json
```

### ขั้นตอน

1. เปิด browser สำหรับ Google OAuth
2. เลือกบัญชี Gmail และอนุญาตสิทธิ์
3. Token จะถูกบันทึกที่ `~/.thanakan/gmail_token.json`

---

## download

ดาวน์โหลด Statement PDF จาก email

### การใช้งาน

```bash
thanakan mail download [OPTIONS] BANK
```

### Arguments

| Argument | ค่าที่รับ | คำอธิบาย |
|----------|----------|----------|
| `BANK` | `kbank`, `bbl`, `scb`, `all` | ธนาคารที่ต้องการดาวน์โหลด |

### Options

| Option | Short | Default | คำอธิบาย |
|--------|-------|---------|----------|
| `--output` | `-o` | `./downloads` | Directory สำหรับบันทึก PDF |
| `--max` | `-m` | `100` | จำนวน email สูงสุดที่จะค้นหา |
| `--parse` | `-p` | `false` | Parse PDF ทันทีหลังดาวน์โหลด |
| `--password` | - | env `PDF_PASS` | รหัสผ่านสำหรับ parse PDF |
| `--metadata/--no-metadata` | - | `true` | บันทึก metadata เป็น JSON |
| `--verbose` | `-v` | `false` | แสดงรายละเอียด |

### ตัวอย่าง

```bash
# ดาวน์โหลดจาก KBank
thanakan mail download kbank

# ดาวน์โหลดจาก BBL พร้อม parse
thanakan mail download bbl --parse --output ./statements

# ดาวน์โหลดจากทุกธนาคาร
thanakan mail download all --max 50

# ไม่บันทึก metadata
thanakan mail download kbank --no-metadata
```

### Output

```
==================================================
Downloading from KBANK
==================================================
KBANK: 15 PDFs from 12 emails

==================================================
TOTAL: 15 PDFs from 12 emails
Saved to: ./downloads
==================================================
```

---

## ธนาคารที่รองรับ

| ธนาคาร | Sender Email |
|--------|--------------|
| KBank | `no-reply@kasikornbank.com` |
| BBL | `estatement@bangkokbank.com` |
| SCB | `scbestatement@scb.co.th` |

---

## การตั้งค่า

### 1. สร้าง Google Cloud Project

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้าง Project ใหม่
3. เปิดใช้งาน Gmail API
4. สร้าง OAuth 2.0 Credentials (Desktop application)
5. ดาวน์โหลด `client_secret.json`

### 2. ตั้งค่า Environment Variables

```bash
# Path ไปยัง client_secret.json (จำเป็น)
export GMAIL_CLIENT_SECRET=/path/to/client_secret.json

# Path สำหรับเก็บ token (optional)
export GMAIL_TOKEN_PATH=~/.thanakan/gmail_token.json

# รหัสผ่าน PDF (optional)
export PDF_PASS=DDMMYYYY
```

### 3. ยืนยันตัวตน

```bash
thanakan mail auth
```

---

## Metadata Format

เมื่อเปิดใช้ `--metadata` จะสร้างไฟล์ `metadata_<bank>.json`:

```json
[
  {
    "message_id": "abc123",
    "subject": "E-Statement ประจำเดือน มกราคม 2024",
    "date": "2024-02-01T10:00:00",
    "sender": "no-reply@kasikornbank.com",
    "downloaded_files": ["statement_202401.pdf"],
    "skipped_attachments": [],
    "errors": []
  }
]
```
