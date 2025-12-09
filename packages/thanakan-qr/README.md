# thanakan-qr

Thai bank slip QR code parser following the SCB specification.

## Installation

```bash
pip install thanakan-qr
```

### System Dependencies

QR parsing requires libzbar:

```bash
# Ubuntu/Debian
sudo apt-get install libzbar0

# macOS
brew install zbar
```

## Usage

### Parse from image

```python
from PIL import Image
from thanakan_qr import SlipQRData

image = Image.open("slip.png")
data = SlipQRData.create_from_image(image)

print(f"Sending Bank: {data.payload.sending_bank_id}")
print(f"Transaction Ref: {data.payload.transaction_ref_id}")
```

### Parse from QR string

```python
from thanakan_qr import SlipQRData

data = SlipQRData.create_from_code("00520102...")
print(data.model_dump_json(indent=2))
```

## API

### SlipQRData

- `SlipQRData.create_from_image(image)` - Parse QR from PIL Image
- `SlipQRData.create_from_code(code)` - Parse QR from string

### Exceptions

- `not_bank_slip` - Raised when QR is not a valid bank slip
- `expect_single_qrcode` - Raised when image has zero or multiple QR codes

## Bank Codes

| Code | Bank |
|------|------|
| `002` | Bangkok Bank (BBL) |
| `004` | Kasikorn Bank (KBank) |
| `006` | Krung Thai Bank (KTB) |
| `011` | TMBThanachart (TTB) |
| `014` | Siam Commercial Bank (SCB) |
| `025` | Bank of Ayudhya (BAY) |

## Documentation

Full documentation: https://ninyawee.github.io/thanakan/libraries/thanakan-qr/
