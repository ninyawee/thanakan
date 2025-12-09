"""Thanakan v2 - Thai bank utilities"""

__version__ = "2.0.0"

# Re-export from sub-libraries
from thanakan_qr import SlipQRData, QrPayload, not_bank_slip, expect_single_qrcode
from thanakan_oauth import KBankAPI, SCBAPI, SCBBaseURL

__all__ = [
    "SlipQRData",
    "QrPayload",
    "not_bank_slip",
    "expect_single_qrcode",
    "KBankAPI",
    "SCBAPI",
    "SCBBaseURL",
]
