# thanakan v2

Thai bank utilities - QR slip parser & bank API clients.

## Breaking Changes in v2

- **Restructured as monorepo with separate sub-packages:**
  - `thanakan-qr` - QR code parser (standalone)
  - `thanakan-oauth` - SCB/KBank API clients (standalone)
- Sub-packages can be installed independently
- Main `thanakan` package re-exports all APIs for backward compatibility

## Installation

```bash
pip install thanakan
# or
uv add thanakan
```

Install only what you need:
```bash
pip install thanakan-qr      # QR parsing only
pip install thanakan-oauth   # Bank APIs only
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

# Parse raw QR code string
thanakan qr --raw "00520102..."

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

## License

MIT
