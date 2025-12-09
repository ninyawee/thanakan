# คำสั่ง accounting

ส่งออก Statement ไปยังโปรแกรมบัญชี

## Alias

```bash
thanakan accounting ...
# หรือ
thanakan acc ...
```

## คำสั่งย่อย

| คำสั่ง | คำอธิบาย |
|--------|----------|
| `peak` | ส่งออกเป็นรูปแบบ Peak Import Statement |

---

## peak

ส่งออก Statement เป็นรูปแบบสำหรับ import เข้า Peak

### การใช้งาน

```bash
thanakan accounting peak [OPTIONS] PATH OUTPUT
```

### Arguments

| Argument | คำอธิบาย |
|----------|----------|
| `PATH` | Path ไปยัง PDF file หรือ directory |
| `OUTPUT` | Path สำหรับ output Excel file (.xlsx) |

### Options

| Option | Short | Default | คำอธิบาย |
|--------|-------|---------|----------|
| `--password` | `-p` | env `PDF_PASS` | รหัสผ่าน PDF |
| `--language` | `-l` | `en` | ภาษาที่ต้องการ: `en`, `th` |
| `--verbose` | `-v` | `false` | แสดงรายละเอียด |

### ตัวอย่าง

```bash
# Export ไฟล์เดียว
thanakan accounting peak statement.pdf peak_import.xlsx

# Export ทั้ง directory
thanakan accounting peak ./statements/ peak_import.xlsx

# ใช้ alias
thanakan acc peak ./statements/ output.xlsx --verbose
```

---

## รูปแบบ Peak Import

ไฟล์ Excel ที่สร้างมีรูปแบบตาม Peak Import Statement:

| Column | ชื่อ | รูปแบบ | ตัวอย่าง |
|--------|------|--------|----------|
| A | วันที่รายการ | YYYYMMDD | `20240115` |
| B | จำนวนเงิน | Number | `-1500.00` (ถอน), `3000.00` (ฝาก) |
| C | หมายเหตุ | Text | `โอนเงิน K PLUS - REF123456` |

### ตัวอย่าง Output

| วันที่รายการ | จำนวนเงิน | หมายเหตุ |
|-------------|-----------|----------|
| 20240115 | -1500.00 | โอนเงิน K PLUS - REF123456 |
| 20240116 | 3000.00 | เงินเข้า - Transfer from BBL |
| 20240117 | -500.00 | PromptPay - 0812345678 |

---

## การ Import เข้า Peak

1. เปิด Peak และไปที่หน้า Bank Statement
2. เลือก "Import Statement"
3. เลือกไฟล์ Excel ที่ export
4. ตรวจสอบและยืนยันการ import

---

## หมายเหตุ

- Output file จะมี sheet แยกต่อบัญชี
- รายการถอนเงินจะแสดงเป็นจำนวนติดลบ (-)
- รายการฝากเงินจะแสดงเป็นจำนวนบวก (+)
- หมายเหตุรวม: คำอธิบาย + ช่องทาง + เลขเช็ค + เลขอ้างอิง
