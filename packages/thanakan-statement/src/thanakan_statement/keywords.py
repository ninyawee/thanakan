"""Hardcoded bilingual keywords for Thai bank statement parsing."""

from enum import Enum


class TransactionType(str, Enum):
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    BALANCE_BEGIN = "balance_begin"
    BALANCE_END = "balance_end"
    CHANNEL = "channel"


# Withdrawal keywords (Thai and English)
WITHDRAWAL_KEYWORDS: list[str] = [
    # KBank - English
    "Transfer Withdrawal",
    "Debit Card Spending",
    "Direct Debit",
    "Annual Debit Card Fee",
    "Payment",
    "PromptPay Transfer",
    "Bill Payment",
    "Fee",
    # KBank - Thai
    "โอนเงิน",
    "ชำระค่าสินค้า",
    "หักบัญชี",
    "ค่าธรรมเนียม",
    "ชำระเงิน",
    "จ่ายบิล",
    "ถอนเงิน",
    # BBL (Bangkok Bank) - English
    "TRF TO OTH BK",
    "PMT. PROMPTPAY",
    "TRF. PROMPTPAY",
    "BILL PAY E-CHN",
    "BILL PAY",
]

# Deposit keywords (Thai and English)
DEPOSIT_KEYWORDS: list[str] = [
    # KBank - English
    "Transfer Deposit",
    "Payment Received",
    "Error Correction",
    "Interest",
    "Refund",
    # KBank - Thai
    "รับโอนเงิน",
    "รับเงิน",
    "ดอกเบี้ย",
    "คืนเงิน",
    "เงินเข้า",
    # BBL (Bangkok Bank) - English
    "TRF FR OTH BK",
    "CASH DEP NBK",
    "CASH DEP",
    "TR FR/TO S/A",
]

# Beginning balance keywords
BALANCE_BEGIN_KEYWORDS: list[str] = [
    "Beginning Balance",
    "ยอดยกมา",
    "B/F",  # BBL: Brought Forward
]

# Ending balance keywords
BALANCE_END_KEYWORDS: list[str] = [
    "Ending Balance",
    "ยอดยกไป",
]

# Channel keywords
CHANNEL_KEYWORDS: list[str] = [
    # KBank
    "K PLUS",
    "K-Plus",
    "EDC",
    "ATM",
    "Internet/Mobile",
    "Automatic Transfer",
    "Online Direct Debit",
    "Counter",
    "Cheque",
    # BBL
    "mPhone",
    "Gtway",
]


def get_balance_keywords() -> dict[str, list[str]]:
    """Get balance keywords grouped by type."""
    return {
        "beginning": BALANCE_BEGIN_KEYWORDS,
        "ending": BALANCE_END_KEYWORDS,
    }


def get_withdrawal_keywords() -> list[str]:
    """Get all withdrawal keywords."""
    return WITHDRAWAL_KEYWORDS


def get_deposit_keywords() -> list[str]:
    """Get all deposit keywords."""
    return DEPOSIT_KEYWORDS


def get_channel_keywords() -> list[str]:
    """Get all channel keywords."""
    return CHANNEL_KEYWORDS
