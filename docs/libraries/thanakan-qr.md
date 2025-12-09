# thanakan-qr

อ่าน QR Code จากสลิปโอนเงินธนาคารไทย ตาม SCB specification

## การติดตั้ง

```bash
pip install thanakan-qr
```

### System Dependencies

ต้องติดตั้ง libzbar:

```bash
# Ubuntu/Debian
sudo apt-get install libzbar0

# macOS
brew install zbar
```

## Quick Start

```python
from PIL import Image
from thanakan_qr import SlipQRData

# อ่านจากรูป
image = Image.open("slip.png")
data = SlipQRData.create_from_image(image)

print(f"ธนาคารผู้โอน: {data.payload.sending_bank_id}")
print(f"เลขอ้างอิง: {data.payload.transaction_ref_id}")
```

## API Reference

### SlipQRData

Class หลักสำหรับ parse QR code จากสลิป

#### Class Methods

##### `create_from_image(image: PIL.Image) -> SlipQRData`

อ่าน QR code จากรูปภาพ

```python
from PIL import Image
from thanakan_qr import SlipQRData

image = Image.open("slip.png")
data = SlipQRData.create_from_image(image)
```

**Raises:**

- `expect_single_qrcode` - ถ้ารูปไม่มี QR หรือมีมากกว่า 1 อัน
- `not_bank_slip` - ถ้า QR ไม่ใช่รูปแบบสลิปธนาคาร

##### `create_from_code(code: str) -> SlipQRData`

อ่านจาก QR code string โดยตรง

```python
from thanakan_qr import SlipQRData

data = SlipQRData.create_from_code("00520102...")
```

**Raises:**

- `not_bank_slip` - ถ้า code ไม่ใช่รูปแบบสลิปธนาคาร

#### Properties

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `raw_code` | `str` | QR code string ดั้งเดิม |
| `payload` | `QrPayload` | ข้อมูลที่ parse แล้ว |

---

### QrPayload

ข้อมูลที่ parse จาก QR code

#### Properties

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `sending_bank_id` | `str` | รหัสธนาคารผู้โอน (3 หลัก) |
| `transaction_ref_id` | `str` | เลขอ้างอิงรายการ |

---

### Exceptions

#### `not_bank_slip`

Raise เมื่อ QR code ไม่ใช่รูปแบบสลิปธนาคาร

```python
from thanakan_qr import SlipQRData, not_bank_slip

try:
    data = SlipQRData.create_from_code("invalid")
except not_bank_slip as e:
    print(f"ไม่ใช่สลิปธนาคาร: {e}")
```

#### `expect_single_qrcode`

Raise เมื่อรูปไม่มี QR code หรือมีมากกว่า 1 อัน

```python
from thanakan_qr import SlipQRData, expect_single_qrcode

try:
    data = SlipQRData.create_from_image(image)
except expect_single_qrcode:
    print("ต้องการ QR code 1 อันเท่านั้น")
```

---

## รหัสธนาคาร

| รหัส | ธนาคาร |
|------|--------|
| `002` | กรุงเทพ (BBL) |
| `004` | กสิกรไทย (KBank) |
| `006` | กรุงไทย (KTB) |
| `011` | ทหารไทยธนชาต (TTB) |
| `014` | ไทยพาณิชย์ (SCB) |
| `025` | กรุงศรีอยุธยา (BAY) |

---

## Export to JSON

```python
from thanakan_qr import SlipQRData

data = SlipQRData.create_from_code("00520102...")

# Export เป็น JSON
json_str = data.model_dump_json(indent=2)
print(json_str)

# Export เป็น dict
dict_data = data.model_dump()
```

Output:

```json
{
  "raw_code": "00520102...",
  "payload": {
    "sending_bank_id": "014",
    "transaction_ref_id": "2024010112345678901234"
  }
}
```
