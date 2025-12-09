# คำสั่ง statement

อ่านและจัดการ PDF Statement จากธนาคาร KBank, BBL และ SCB

## Alias

```bash
thanakan statement ...
# หรือ
thanakan stm ...
```

## คำสั่งย่อย

| คำสั่ง | คำอธิบาย |
|--------|----------|
| `parse` | อ่าน Statement PDF และแสดงผลเป็น JSON |
| `export` | อ่านและ export เป็นไฟล์ (JSON, CSV, Excel) |
| `validate` | ตรวจสอบความต่อเนื่องของยอดเงิน |

---

## parse

อ่าน Statement PDF และแสดงผลเป็น JSON

### การใช้งาน

```bash
thanakan statement parse [OPTIONS] PATH
```

### Arguments

| Argument | คำอธิบาย |
|----------|----------|
| `PATH` | Path ไปยัง PDF file หรือ directory |

### Options

| Option | Short | คำอธิบาย |
|--------|-------|----------|
| `--password` | `-p` | รหัสผ่าน PDF (default: env `PDF_PASS`) |
| `--verbose` | `-v` | แสดงรายละเอียดการ parse |

### ตัวอย่าง

```bash
# อ่านไฟล์เดียว
thanakan statement parse statement.pdf

# อ่านทั้ง directory
thanakan statement parse ./statements/

# ระบุรหัสผ่าน
thanakan statement parse statement.pdf --password "mypassword"
```

---

## export

อ่าน Statement และ export เป็นไฟล์

### การใช้งาน

```bash
thanakan statement export [OPTIONS] PATH OUTPUT
```

### Arguments

| Argument | คำอธิบาย |
|----------|----------|
| `PATH` | Path ไปยัง PDF file หรือ directory |
| `OUTPUT` | Path สำหรับ output (file หรือ directory) |

### Options

| Option | Short | คำอธิบาย |
|--------|-------|----------|
| `--format` | `-f` | รูปแบบ output: `json`, `csv`, `excel` (default: `json`) |
| `--password` | `-p` | รหัสผ่าน PDF |
| `--language` | `-l` | ภาษาที่ต้องการสำหรับ statement ที่ซ้ำกัน: `en`, `th` (default: `en`) |
| `--verbose` | `-v` | แสดงรายละเอียด |

### ตัวอย่าง

```bash
# Export เป็น JSON
thanakan statement export ./pdfs/ output.json

# Export เป็น Excel
thanakan statement export ./pdfs/ output.xlsx --format excel

# Export เป็น CSV (หลายไฟล์ต่อบัญชี)
thanakan statement export ./pdfs/ ./csv_output/ --format csv

# เลือกภาษาไทย
thanakan statement export ./pdfs/ output.json --language th
```

### รูปแบบ Output

| Format | คำอธิบาย |
|--------|----------|
| `json` | ไฟล์ JSON เดียว รวมทุกบัญชี |
| `csv` | Directory ที่มี CSV แยกต่อบัญชี |
| `excel` | ไฟล์ Excel เดียว แยก sheet ต่อบัญชี |

---

## validate

ตรวจสอบความต่อเนื่องของยอดเงินระหว่าง Statement

### การใช้งาน

```bash
thanakan statement validate [OPTIONS] PATH
```

### Arguments

| Argument | คำอธิบาย |
|----------|----------|
| `PATH` | Path ไปยัง PDF file หรือ directory |

### Options

| Option | Short | คำอธิบาย |
|--------|-------|----------|
| `--password` | `-p` | รหัสผ่าน PDF |

### ตัวอย่าง

```bash
thanakan statement validate ./statements/
```

### Output

```
[OK] 123-4-56789-0: 12 statements validated
[FAIL] 987-6-54321-0: 1 issue(s) found
  - statement_202401.pdf: expected opening 10000.00, got 9500.00
```

---

## ธนาคารที่รองรับ

| ธนาคาร | รูปแบบ Statement |
|--------|-----------------|
| KBank | PDF ภาษาไทยและอังกฤษ |
| BBL | PDF ภาษาไทยและอังกฤษ |
| SCB | PDF ภาษาไทยและอังกฤษ |

## หมายเหตุ

- Statement PDF ส่วนใหญ่มีรหัสผ่านเป็นวันเดือนปีเกิด (DDMMYYYY)
- สามารถตั้งค่า environment variable `PDF_PASS` แทนการระบุทุกครั้ง
