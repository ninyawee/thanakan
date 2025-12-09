# CLI Commands

Thanakan CLI ประกอบด้วยคำสั่งหลัก 4 กลุ่ม:

| คำสั่ง | Alias | คำอธิบาย |
|--------|-------|----------|
| `thanakan qr` | - | อ่าน QR Code จากสลิปโอนเงิน |
| `thanakan statement` | `stm` | อ่านและจัดการ Statement PDF |
| `thanakan mail` | - | ดาวน์โหลด Statement จาก Gmail |
| `thanakan accounting` | `acc` | ส่งออกไปยังโปรแกรมบัญชี |

## การใช้งานพื้นฐาน

```bash
# แสดง help
thanakan --help

# แสดง help ของคำสั่งย่อย
thanakan qr --help
thanakan statement --help

# แสดงเวอร์ชัน
thanakan version
```

## ภาพรวมคำสั่ง

### QR Command

อ่าน QR Code จากรูปสลิปหรือ string:

```bash
thanakan qr slip.png
thanakan qr --raw "00520102..."
```

[ดูรายละเอียด](qr.md)

### Statement Commands

อ่าน, export, และตรวจสอบ Statement PDF:

```bash
thanakan statement parse statement.pdf
thanakan statement export ./pdfs/ output.xlsx --format excel
thanakan statement validate ./pdfs/
```

[ดูรายละเอียด](statement.md)

### Mail Commands

ดาวน์โหลด Statement จาก Gmail:

```bash
thanakan mail auth
thanakan mail download kbank
```

[ดูรายละเอียด](mail.md)

### Accounting Commands

ส่งออกไปยังโปรแกรมบัญชี:

```bash
thanakan accounting peak ./pdfs/ output.xlsx
```

[ดูรายละเอียด](accounting.md)
