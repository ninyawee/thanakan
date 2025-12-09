# Thanakan

**Thai Bank Utilities** - เครื่องมือสำหรับจัดการข้อมูลธนาคารไทย

## ความสามารถหลัก

- **QR Parser** - อ่าน QR Code จากสลิปโอนเงินธนาคารไทย
- **Bank API Clients** - เชื่อมต่อ API ของ SCB และ KBank สำหรับตรวจสอบสลิป
- **Statement Parser** - อ่านและแปลง PDF Statement จาก KBank, BBL และ SCB
- **Mail Downloader** - ดาวน์โหลด Statement PDF จาก Gmail อัตโนมัติ
- **Accounting Export** - ส่งออกข้อมูลไปยังโปรแกรมบัญชี (Peak)

## โครงสร้าง Package

Thanakan เป็น monorepo ประกอบด้วย package ย่อยที่สามารถติดตั้งแยกกันได้:

| Package | คำอธิบาย |
|---------|----------|
| `thanakan` | Package หลัก รวม CLI และ re-export ทุก API |
| `thanakan-qr` | อ่าน QR Code จากสลิปธนาคาร |
| `thanakan-oauth` | API clients สำหรับ SCB และ KBank |
| `thanakan-statement` | อ่าน PDF Statement (KBank, BBL, SCB) |
| `thanakan-mail` | ดาวน์โหลด Statement จาก Gmail |
| `thanakan-accounting` | ส่งออกไปยังโปรแกรมบัญชี |

## ติดตั้งด่วน

```bash
# ติดตั้งทุก feature
pip install thanakan

# หรือติดตั้งเฉพาะที่ต้องการ
pip install thanakan-qr        # QR parsing เท่านั้น
pip install thanakan-oauth     # Bank APIs เท่านั้น
pip install thanakan-statement # Statement parsing เท่านั้น
```

### ใช้งานทันทีด้วย uvx (ไม่ต้องติดตั้ง)

```bash
uvx thanakan qr slip.png
uvx thanakan statement parse statement.pdf
```

## ตัวอย่างการใช้งาน

### CLI

```bash
# อ่าน QR จากรูปสลิป
thanakan qr slip.png

# อ่าน Statement PDF
thanakan statement parse statement.pdf

# ดาวน์โหลด Statement จาก Gmail
thanakan mail download kbank
```

### Python

```python
from thanakan import SlipQRData, SCBAPI

# อ่าน QR จากรูป
from PIL import Image
image = Image.open("slip.png")
data = SlipQRData.create_from_image(image)
print(data.payload.transaction_ref_id)

# ตรวจสอบสลิปกับ SCB API
api = SCBAPI(app_key, app_secret, cert=cert_path)
result = await api.verify_slip(sending_bank_id, transaction_ref)
```

## เริ่มต้นใช้งาน

ดูรายละเอียดการติดตั้งและตั้งค่าที่หน้า [เริ่มต้นใช้งาน](getting-started.md)

---

โปรเจกต์นี้พัฒนาโดย [SAA-Coop](https://github.com/SAA-Coop)
