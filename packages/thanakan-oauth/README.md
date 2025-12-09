# thanakan-oauth

Thai bank OAuth API clients for SCB and KBank.

## Installation

```bash
pip install thanakan-oauth
```

## Usage

### SCB API

```python
from thanakan_oauth import SCBAPI, SCBBaseURL

api = SCBAPI(
    app_key="your_app_key",
    app_secret="your_app_secret",
    cert="/path/to/cert.pem",
    base_url=SCBBaseURL.PRODUCTION
)

# Verify slip
result = await api.verify_slip(
    sending_bank_id="014",
    transaction_ref_id="2024010112345678901234"
)

if result.data:
    print(f"Amount: {result.data.amount}")
    print(f"Sender: {result.data.sender.name}")
```

### KBank API

```python
from thanakan_oauth import KBankAPI

api = KBankAPI(
    consumer_id="your_consumer_id",
    consumer_secret="your_consumer_secret",
    cert="/path/to/cert.pem"
)

# Verify slip (async)
result = await api.verify_slip(
    sending_bank_id="014",
    transaction_ref_id="2024010112345678901234"
)

# Verify slip (sync)
result = api.verify_slip_sync(
    sending_bank_id="014",
    transaction_ref_id="2024010112345678901234"
)
```

## SCB API Methods

- `verify_slip(sending_bank_id, transaction_ref_id)` - Verify transfer slip
- `create_qr30(amount, ref1, ref2, ref3)` - Generate QR30 payment code
- `query_transaction(biller_id, reference1, transaction_date)` - Query transaction
- `create_deeplink(amount, ref1, ref2, ref3)` - Create SCB Easy deeplink
- `get_deeplink(transaction_id)` - Get deeplink details

## KBank API Methods

- `verify_slip(sending_bank_id, transaction_ref_id)` - Verify transfer slip (async)
- `verify_slip_sync(sending_bank_id, transaction_ref_id)` - Verify transfer slip (sync)

## mTLS Certificate

Both APIs require mTLS certificates for production:

```python
# Single file (cert + key combined)
api = SCBAPI(..., cert="/path/to/combined.pem")

# Separate cert and key
api = SCBAPI(..., cert=("/path/to/cert.pem", "/path/to/key.pem"))
```

## Documentation

Full documentation: https://ninyawee.github.io/thanakan/libraries/thanakan-oauth/
