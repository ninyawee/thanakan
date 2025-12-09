# thanakan v2

[![PyPI](https://img.shields.io/pypi/v/thanakan)](https://pypi.org/project/thanakan/)
[![Sigstore](https://img.shields.io/badge/sigstore-signed-blue?logo=sigstore)](https://pypi.org/project/thanakan/#attestations)
[![Documentation](https://img.shields.io/badge/docs-ninyawee.github.io%2Fthanakan-blue)](https://ninyawee.github.io/thanakan)

Thai bank utilities - QR slip parser, bank API clients, statement parser & more.

**[Documentation](https://ninyawee.github.io/thanakan)** | **[GitHub](https://github.com/ninyawee/thanakan)**

## Breaking Changes in v2

- **Restructured as monorepo with separate sub-packages:**
  - `thanakan-qr` - QR code parser (standalone)
  - `thanakan-oauth` - SCB/KBank API clients (standalone)
  - `thanakan-statement` - PDF statement parser for KBank/BBL/SCB (standalone)
  - `thanakan-mail` - Download statements from Gmail (standalone)
  - `thanakan-accounting` - Export to accounting software (standalone)
- Sub-packages can be installed independently
- Main `thanakan` package re-exports all APIs for backward compatibility

## Installation

```bash
pip install thanakan
# or
uv add thanakan
```

### Global install

```bash
uv tool install thanakan
# or
mise use -g pipx:thanakan
# or
pipx install thanakan
```

### Run without installing (uvx)

```bash
uvx thanakan qr slip.png
uvx thanakan statement parse statement.pdf
```

### Install only what you need
```bash
pip install thanakan-qr         # QR parsing only
pip install thanakan-oauth      # Bank APIs only
pip install thanakan-statement  # PDF statement parsing only
pip install thanakan-mail       # Gmail download only
pip install thanakan-accounting # Accounting export only
```

### System Dependencies

QR parsing requires libzbar:
```bash
# Ubuntu/Debian
sudo apt-get install libzbar0

# macOS
brew install zbar
```

## CLI Usage

```bash
# Parse QR from slip image
thanakan qr slip.png

# Parse QR from stdin (text or image)
pbpaste | thanakan qr          # macOS clipboard
echo "00520102..." | thanakan qr
cat slip.png | thanakan qr

# Pipe to jq (outputs compact JSON when piped)
thanakan qr slip.png | jq .payload

# Parse PDF statement
thanakan statement parse statement.pdf

# Export statements to Excel
thanakan statement export ./pdfs/ output.xlsx --format excel

# Download statements from Gmail
thanakan mail download kbank

# Export to Peak accounting format
thanakan accounting peak ./pdfs/ peak_import.xlsx

# Show version
thanakan version
```

## Python Usage

```python
# Using main package (recommended)
from thanakan import SlipQRData, SCBAPI, KBankAPI

# Or import from sub-packages directly
from thanakan_qr import SlipQRData
from thanakan_oauth import SCBAPI, KBankAPI
```

### Parse QR from image

```python
from PIL import Image
from thanakan import SlipQRData

image = Image.open("slip.png")
data = SlipQRData.create_from_image(image)
print(data.payload.sending_bank_id)
print(data.payload.transaction_ref_id)
```

### Parse raw QR code

```python
from thanakan import SlipQRData

data = SlipQRData.create_from_code("00520102...")
print(data.model_dump_json(indent=2))
```

## Credits

This project is a work of [SAA-Coop](https://github.com/SAA-Coop).

## License

MIT
