from thanakan_statement.parser import BANK_KBANK, BANK_SCB, detect_bank_type

KBANK_WITH_SCB_MERCHANT = """ชื่อบัญชี นาย ณัฐชนน นินยวี เลขที่บัญชีเงินฝาก 219-8-82296-8
รอบระหว่างวันที่ 01/09/2026 - 30/09/2026
01-09-26 ยอดยกมา 227,112.40
03-09-26 20:22 ชำระเงิน 175.00 221,837.40 K PLUS เพื่อชำระ Ref X8130 SCB มณี SHOP
"""


def test_kbank_paying_scb_merchant_stays_kbank():
    assert detect_bank_type(KBANK_WITH_SCB_MERCHANT) == BANK_KBANK


def test_scb_header_detected():
    assert detect_bank_type("SIAM COMMERCIAL BANK\n01/04/24 19:20 X2 ENET 3,470.00 42,072.00") == BANK_SCB
