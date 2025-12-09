# คำสั่ง qr

อ่าน QR Code จากสลิปโอนเงินธนาคารไทย ตาม SCB specification

## การใช้งาน

```bash
thanakan qr [OPTIONS] [IMAGE]
```

## Arguments

| Argument | คำอธิบาย |
|----------|----------|
| `IMAGE` | Path ไปยังไฟล์รูปสลิป (PNG, JPG, etc.) |

## Options

| Option | Short | คำอธิบาย |
|--------|-------|----------|
| `--raw` | `-r` | QR code string โดยตรง (ไม่ต้องใช้รูป) |
| `--verbose` | `-v` | แสดงข้อมูลเพิ่มเติมและขั้นตอนถัดไป |

## ตัวอย่าง

### อ่านจากไฟล์รูป

```bash
thanakan qr slip.png
```

ผลลัพธ์:

```json
{
  "raw_code": "00520102...",
  "payload": {
    "sending_bank_id": "014",
    "transaction_ref_id": "2024010112345678901234"
  }
}
```

### อ่านจาก QR string โดยตรง

```bash
thanakan qr --raw "00520102..."
```

### แสดงข้อมูลเพิ่มเติม

```bash
thanakan qr slip.png --verbose
```

จะแสดงขั้นตอนถัดไปสำหรับการตรวจสอบสลิปกับ Bank API

## Output Format

ผลลัพธ์เป็น JSON ประกอบด้วย:

| Field | คำอธิบาย |
|-------|----------|
| `raw_code` | QR code string ดั้งเดิม |
| `payload.sending_bank_id` | รหัสธนาคารผู้โอน (3 หลัก) |
| `payload.transaction_ref_id` | เลขอ้างอิงรายการ |

## รหัสธนาคาร

| รหัส | ธนาคาร |
|------|--------|
| `002` | กรุงเทพ (BBL) |
| `004` | กสิกรไทย (KBank) |
| `006` | กรุงไทย (KTB) |
| `011` | ทหารไทยธนชาต (TTB) |
| `014` | ไทยพาณิชย์ (SCB) |
| `025` | กรุงศรีอยุธยา (BAY) |

## Error Handling

### ไม่พบ QR Code

```
Error: Expected exactly one QR code in image
```

สาเหตุ:
- รูปไม่มี QR code
- รูปมี QR code มากกว่า 1 อัน
- QR code เบลอหรือเสียหาย

### QR ไม่ใช่สลิปธนาคาร

```
Error: Not a valid bank slip QR
```

สาเหตุ:
- QR code ไม่ใช่รูปแบบสลิปธนาคารไทย
- ข้อมูล QR เสียหาย
- CRC checksum ไม่ตรง

## System Requirements

ต้องติดตั้ง libzbar:

```bash
# Ubuntu/Debian
sudo apt-get install libzbar0

# macOS
brew install zbar
```
