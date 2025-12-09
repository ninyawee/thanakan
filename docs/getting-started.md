# เริ่มต้นใช้งาน

## การติดตั้ง

### ติดตั้งด้วย pip

```bash
pip install thanakan
```

### ติดตั้งด้วย uv

```bash
uv add thanakan
```

### ติดตั้งแบบ Global

```bash
# ด้วย uv
uv tool install thanakan

# ด้วย mise
mise use -g pipx:thanakan

# ด้วย pipx
pipx install thanakan
```

### ใช้งานโดยไม่ต้องติดตั้ง (uvx)

```bash
# รัน CLI โดยตรงด้วย uvx
uvx thanakan qr slip.png
uvx thanakan statement parse statement.pdf
uvx thanakan version
```

### ติดตั้งเฉพาะ package ที่ต้องการ

```bash
# QR parsing เท่านั้น
pip install thanakan-qr

# Bank APIs เท่านั้น
pip install thanakan-oauth

# Statement parsing เท่านั้น
pip install thanakan-statement

# Mail download เท่านั้น
pip install thanakan-mail

# Accounting export เท่านั้น
pip install thanakan-accounting
```

## System Dependencies

### libzbar (สำหรับ QR parsing)

QR parsing ต้องการ libzbar:

=== "Ubuntu/Debian"

    ```bash
    sudo apt-get install libzbar0
    ```

=== "macOS"

    ```bash
    brew install zbar
    ```

=== "Windows"

    ดาวน์โหลดจาก [ZBar Windows](http://zbar.sourceforge.net/download.html)

## ตรวจสอบการติดตั้ง

```bash
thanakan version
```

ควรแสดงเวอร์ชันปัจจุบัน เช่น `thanakan 2.0.0`

## Quick Start

### 1. อ่าน QR จากสลิปโอนเงิน

```bash
# จากไฟล์รูป
thanakan qr slip.png

# จาก QR string โดยตรง
thanakan qr --raw "00520102..."
```

ผลลัพธ์จะเป็น JSON:

```json
{
  "raw_code": "00520102...",
  "payload": {
    "sending_bank_id": "014",
    "transaction_ref_id": "2024010112345678901234"
  }
}
```

### 2. อ่าน Statement PDF

```bash
# อ่านไฟล์เดียว
thanakan statement parse statement.pdf

# อ่านทั้ง directory
thanakan statement parse ./statements/

# Export เป็น Excel
thanakan statement export ./statements/ output.xlsx --format excel
```

### 3. ใช้งานใน Python

```python
from thanakan import SlipQRData

# อ่าน QR จากรูป
from PIL import Image
image = Image.open("slip.png")
data = SlipQRData.create_from_image(image)

print(f"ธนาคารผู้โอน: {data.payload.sending_bank_id}")
print(f"เลขอ้างอิง: {data.payload.transaction_ref_id}")
```

## ขั้นตอนถัดไป

- [CLI Commands](cli/index.md) - ดูคำสั่ง CLI ทั้งหมด
- [Libraries](libraries/index.md) - ใช้งาน library ใน Python
