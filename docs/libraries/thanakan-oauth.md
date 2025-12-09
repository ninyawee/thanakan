# thanakan-oauth

API clients สำหรับ SCB และ KBank

## การติดตั้ง

```bash
pip install thanakan-oauth
```

## Quick Start

```python
from thanakan_oauth import SCBAPI, KBankAPI

# SCB API
scb = SCBAPI(
    app_key="your_app_key",
    app_secret="your_app_secret",
    cert="/path/to/cert.pem"
)

# KBank API
kbank = KBankAPI(
    consumer_id="your_consumer_id",
    consumer_secret="your_consumer_secret",
    cert="/path/to/cert.pem"
)
```

---

## SCBAPI

API client สำหรับ SCB Developer API

### Constructor

```python
SCBAPI(
    app_key: str,
    app_secret: str,
    biller_id: str | None = None,
    merchant_id: str | None = None,
    terminal_id: str | None = None,
    cert: str | tuple[str, str] | None = None,
    base_url: SCBBaseURL = SCBBaseURL.SANDBOX
)
```

| Parameter | คำอธิบาย |
|-----------|----------|
| `app_key` | Application Key จาก SCB Developer |
| `app_secret` | Application Secret |
| `biller_id` | Biller ID (สำหรับ QR30) |
| `merchant_id` | Merchant ID |
| `terminal_id` | Terminal ID |
| `cert` | Path ไปยัง mTLS certificate |
| `base_url` | `SCBBaseURL.SANDBOX` หรือ `SCBBaseURL.PRODUCTION` |

### Methods

#### `verify_slip`

ตรวจสอบสลิปโอนเงิน

```python
result = await scb.verify_slip(
    sending_bank_id="014",
    transaction_ref_id="2024010112345678901234"
)

if result.data:
    print(f"จำนวนเงิน: {result.data.amount}")
    print(f"ผู้โอน: {result.data.sender.name}")
```

#### `create_qr30`

สร้าง QR Code สำหรับรับชำระเงิน (QR30)

```python
result = await scb.create_qr30(
    amount=100.00,
    ref1="INV001",
    ref2="CUST001",
    ref3="ORDER001"
)

print(f"QR Data: {result.data.qr_raw_data}")
print(f"QR Image: {result.data.qr_image}")
```

#### `query_transaction`

ค้นหารายการ transaction

```python
result = await scb.query_transaction(
    biller_id="your_biller_id",
    reference1="INV001",
    transaction_date="20240115"
)
```

#### `create_deeplink`

สร้าง deeplink สำหรับชำระเงินผ่าน SCB Easy

```python
result = await scb.create_deeplink(
    amount=100.00,
    ref1="INV001",
    ref2="CUST001",
    ref3="ORDER001"
)

print(f"Deeplink: {result.data.deeplink_url}")
```

#### `get_deeplink`

ดึงข้อมูล deeplink ที่สร้างไว้

```python
result = await scb.get_deeplink(transaction_id="xxx")
```

### Sync Methods

ทุก method มี sync version โดยเติม `_sync`:

```python
# Async
result = await scb.verify_slip(...)

# Sync
result = scb.verify_slip_sync(...)
```

---

## KBankAPI

API client สำหรับ KBank Open API

### Constructor

```python
KBankAPI(
    consumer_id: str,
    consumer_secret: str,
    cert: str | tuple[str, str] | None = None
)
```

| Parameter | คำอธิบาย |
|-----------|----------|
| `consumer_id` | Consumer ID จาก KBank Developer |
| `consumer_secret` | Consumer Secret |
| `cert` | Path ไปยัง mTLS certificate |

### Methods

#### `verify_slip`

ตรวจสอบสลิปโอนเงิน

```python
# Async
result = await kbank.verify_slip(
    sending_bank_id="014",
    transaction_ref_id="2024010112345678901234"
)

# Sync
result = kbank.verify_slip_sync(
    sending_bank_id="014",
    transaction_ref_id="2024010112345678901234"
)

if result.data:
    print(f"จำนวนเงิน: {result.data.amount}")
    print(f"ผู้โอน: {result.data.sender.name}")
```

---

## SlipData

Response model ที่ใช้ร่วมกันระหว่าง SCB และ KBank

### Properties

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `sender` | `End` | ข้อมูลผู้โอน |
| `receiver` | `End` | ข้อมูลผู้รับ |
| `amount` | `Decimal` | จำนวนเงิน |
| `transaction_date_time` | `datetime` | วันเวลาทำรายการ |
| `transaction_id` | `str` | รหัสรายการ |

### End (ข้อมูลผู้โอน/ผู้รับ)

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `name` | `str` | ชื่อ |
| `account` | `Account` | ข้อมูลบัญชี |
| `proxy` | `Proxy` | ข้อมูล PromptPay (ถ้ามี) |

---

## mTLS Certificate

ทั้ง SCB และ KBank ต้องใช้ mTLS certificate สำหรับ production:

```python
# Path เดียว (cert + key รวมกัน)
api = SCBAPI(..., cert="/path/to/combined.pem")

# แยก cert และ key
api = SCBAPI(..., cert=("/path/to/cert.pem", "/path/to/key.pem"))
```

---

## Error Handling

```python
from thanakan_oauth import SCBAPI

api = SCBAPI(...)

try:
    result = await api.verify_slip(...)
except ConnectionError as e:
    print(f"Connection error: {e}")

# ตรวจสอบ response status
if result.status.code != 1000:
    print(f"Error: {result.status.description}")
```
