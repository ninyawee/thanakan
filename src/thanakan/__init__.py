"""Thanakan v2 - Thai bank utilities"""

__version__ = "2.0.0"

# Re-exported lazily so the CLI's statement/mail commands don't need libzbar (thanakan_qr)
_EXPORTS = {
    "SlipQRData": "thanakan_qr",
    "QrPayload": "thanakan_qr",
    "not_bank_slip": "thanakan_qr",
    "expect_single_qrcode": "thanakan_qr",
    "KBankAPI": "thanakan_oauth",
    "SCBAPI": "thanakan_oauth",
    "SCBBaseURL": "thanakan_oauth",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name in _EXPORTS:
        import importlib

        return getattr(importlib.import_module(_EXPORTS[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
