"""Parse Thai bank PDF statements and extract transaction data."""

import io
import os
import re
from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pdfplumber
import pikepdf

from .models import Statement, Transaction
from .keywords import (
    get_balance_keywords,
    get_channel_keywords,
    get_deposit_keywords,
    get_withdrawal_keywords,
)

# Default PDF password (from environment or fallback)
DEFAULT_PASSWORD = os.environ.get("PDF_PASS", "DDMMYYYY")

# Bank type constants
BANK_KBANK = "kbank"
BANK_BBL = "bbl"
BANK_SCB = "scb"


def detect_bank_type(text: str) -> str:
    """Detect bank type from PDF content.

    Args:
        text: Full PDF text content

    Returns:
        Bank type: "scb", "bbl", or "kbank" (default)
    """
    if "SIAM COMMERCIAL" in text or "ไทยพาณิชย์" in text or "SCB" in text:
        return BANK_SCB
    if "Bangkok Bank" in text or "ธนาคารกรุงเทพ" in text or "Bualuang" in text:
        return BANK_BBL
    return BANK_KBANK  # default


def detect_pdf_language(text: str) -> str:
    """Detect whether PDF is Thai or English based on text content.

    Uses header/label keywords to determine language since transaction
    descriptions can be in either language regardless of statement language.

    Args:
        text: Full PDF text content

    Returns:
        "th" for Thai, "en" for English
    """
    # Thai-specific header/label keywords (not transaction descriptions)
    thai_header_keywords = [
        "ยอดยกมา",  # Beginning balance
        "ยอดยกไป",  # Ending balance
        "รอบระหว่างวันที่",  # Period
        "ชื่อบัญชี",  # Account name
        "เลขที่บัญชี",  # Account number
        "ยอดรวมถอน",  # Total withdrawal
        "ยอดรวมฝาก",  # Total deposit
        "ยอดคงเหลือ",  # Balance
        "รายละเอียด",  # Details
    ]

    # English-specific header/label keywords
    english_header_keywords = [
        "Beginning Balance",
        "Ending Balance",
        "Period",
        "Account Number",
        "Account Name",
        "Total Withdrawal",
        "Total Deposit",
        "Outstanding Balance",
        "Descriptions",
    ]

    thai_keyword_count = sum(1 for kw in thai_header_keywords if kw in text)
    english_keyword_count = sum(1 for kw in english_header_keywords if kw in text)

    # Prefer keyword matching over character counting
    if thai_keyword_count > english_keyword_count:
        return "th"
    if english_keyword_count > thai_keyword_count:
        return "en"

    # Fallback: count Thai characters in significant portions
    # (Thai headers tend to have more Thai characters than just addresses)
    thai_char_count = sum(1 for char in text if "\u0e00" <= char <= "\u0e7f")
    if thai_char_count > 200:
        return "th"

    return "en"


def decrypt_pdf(pdf_path: Path | str, password: str = DEFAULT_PASSWORD) -> bytes:
    """Decrypt a password-protected PDF.

    Args:
        pdf_path: Path to encrypted PDF
        password: PDF password

    Returns:
        Decrypted PDF bytes
    """
    with pikepdf.open(pdf_path, password=password) as pdf:
        output = io.BytesIO()
        pdf.save(output)
        return output.getvalue()


def parse_date(date_str: str) -> date:
    """Parse date from DD-MM-YY format.

    Args:
        date_str: Date string (e.g., "01-11-25")

    Returns:
        date object
    """
    day, month, year = date_str.split("-")
    # Assume 20xx for 2-digit years
    full_year = 2000 + int(year)
    return date(full_year, int(month), int(day))


def parse_time(time_str: str) -> time | None:
    """Parse time from HH:MM format.

    Args:
        time_str: Time string (e.g., "14:30")

    Returns:
        time object or None
    """
    if not time_str:
        return None
    try:
        hour, minute = time_str.split(":")
        return time(int(hour), int(minute))
    except (ValueError, AttributeError):
        return None


def parse_amount(amount_str: str) -> Decimal | None:
    """Parse amount string to Decimal.

    Args:
        amount_str: Amount string (e.g., "8,400.00")

    Returns:
        Decimal value or None
    """
    if not amount_str or amount_str.strip() == "":
        return None
    cleaned = amount_str.replace(",", "").strip()
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def extract_account_info(text: str) -> tuple[str | None, str | None, date | None, date | None]:
    """Extract account info from PDF header text.

    Returns:
        (account_number, account_name, period_start, period_end)
    """
    account_number = None
    account_name = None
    period_start = None
    period_end = None

    # Account number pattern: XXX-X-XXXXX-X
    acc_match = re.search(r"(\d{3}-\d-\d{5}-\d)", text)
    if acc_match:
        account_number = acc_match.group(1)

    # Period pattern: "Period DD/MM/YYYY - DD/MM/YYYY" (English)
    # or "รอบระหว่างวันที่ DD/MM/YYYY - DD/MM/YYYY" (Thai)
    period_match = re.search(r"(?:Period|รอบระหว่างวันที่)\s+(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", text)
    if period_match:
        # Parse DD/MM/YYYY format
        start_parts = period_match.group(1).split("/")
        end_parts = period_match.group(2).split("/")
        period_start = date(int(start_parts[2]), int(start_parts[1]), int(start_parts[0]))
        period_end = date(int(end_parts[2]), int(end_parts[1]), int(end_parts[0]))

    # Account name - pattern "AccountMR. Name..." or "ชื่อบัญชี นาย/นาง/น.ส. Name"
    name_match = re.search(r"Account\s*(MR\.|MS\.|MRS\.)\s*(.+?)(?:\s+Reference|$)", text)
    if name_match:
        account_name = f"{name_match.group(1)} {name_match.group(2)}".strip()
    else:
        # Thai pattern: ชื่อบัญชี นาย/นาง/น.ส. Name
        name_match = re.search(r"ชื่อบัญชี\s+(นาย|นาง|น\.ส\.)\s+(.+?)(?:\s+เลขที่|$)", text)
        if name_match:
            # Convert Thai prefix to English
            prefix_map = {"นาย": "MR.", "นาง": "MRS.", "น.ส.": "MS."}
            prefix = prefix_map.get(name_match.group(1), name_match.group(1))
            account_name = f"{prefix} {name_match.group(2)}".strip()
        else:
            name_match = re.search(r"Account Name\s*:\s*(.+?)(?:\n|Account)", text)
            if name_match:
                account_name = name_match.group(1).strip()

    return account_number, account_name, period_start, period_end


def extract_balances(text: str) -> tuple[Decimal | None, Decimal | None]:
    """Extract opening and closing balances (Thai/English).

    Returns:
        (opening_balance, closing_balance)
    """
    opening = None
    closing = None
    balance_keywords = get_balance_keywords()

    # Beginning Balance (English or Thai)
    for keyword in balance_keywords["beginning"]:
        begin_match = re.search(rf"{re.escape(keyword)}\s+([\d,]+\.\d{{2}})", text)
        if begin_match:
            opening = parse_amount(begin_match.group(1))
            break

    # Ending Balance (English or Thai)
    for keyword in balance_keywords["ending"]:
        end_match = re.search(rf"{re.escape(keyword)}\s+([\d,]+\.\d{{2}})", text)
        if end_match:
            closing = parse_amount(end_match.group(1))
            break

    return opening, closing


def parse_transaction_line(line: str) -> Transaction | None:
    """Parse a single KBank transaction line.

    Args:
        line: Transaction line text

    Returns:
        Transaction object or None
    """
    # Pattern: DD-MM-YY [HH:MM] DESCRIPTION AMOUNT(S) BALANCE CHANNEL DETAILS
    date_pattern = re.compile(r"^(\d{2}-\d{2}-\d{2})\s+")
    match = date_pattern.match(line)
    if not match:
        return None

    date_str = match.group(1)

    # Skip Beginning/Ending Balance lines (Thai and English)
    balance_keywords = get_balance_keywords()
    balance_skip_keywords = balance_keywords["beginning"] + balance_keywords["ending"]
    if any(kw in line for kw in balance_skip_keywords):
        return None

    try:
        txn_date = parse_date(date_str)
    except Exception:
        return None

    # Extract time if present
    time_match = re.search(r"^\d{2}-\d{2}-\d{2}\s+(\d{2}:\d{2})\s+", line)
    txn_time = parse_time(time_match.group(1)) if time_match else None

    # Find all amounts (numbers with commas and decimals)
    amount_pattern = re.compile(r"([\d,]+\.\d{2})")
    amounts = amount_pattern.findall(line)

    if not amounts:
        return None

    # Extract description (between date/time and first amount)
    if txn_time:
        desc_match = re.search(r"^\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+(.+?)(?:\d[\d,]*\.\d{2})", line)
    else:
        desc_match = re.search(r"^\d{2}-\d{2}-\d{2}\s+(.+?)(?:\d[\d,]*\.\d{2})", line)

    description = desc_match.group(1).strip() if desc_match else ""

    # Determine transaction type and amounts
    withdrawal = None
    deposit = None
    balance = None

    # Use keyword lists for bilingual support
    withdrawal_keywords = get_withdrawal_keywords()
    deposit_keywords = get_deposit_keywords()
    is_withdrawal = any(kw in line for kw in withdrawal_keywords) and not any(kw in line for kw in deposit_keywords)
    is_deposit = any(kw in line for kw in deposit_keywords)

    if len(amounts) >= 2:
        # Usually: amount, balance
        if is_withdrawal:
            withdrawal = parse_amount(amounts[0])
            balance = parse_amount(amounts[-1])
        elif is_deposit:
            deposit = parse_amount(amounts[0])
            balance = parse_amount(amounts[-1])
        else:
            # Default: try to guess from position
            balance = parse_amount(amounts[-1])
            # If balance decreased, it's a withdrawal
            # We'll need to track balance to know for sure
            withdrawal = parse_amount(amounts[0])
    elif len(amounts) == 1:
        balance = parse_amount(amounts[0])

    if balance is None:
        return None

    # Extract channel using keywords
    channel = None
    channel_keywords = get_channel_keywords()
    for kw in channel_keywords:
        if kw.lower() in line.lower():
            channel = kw
            break

    # Extract reference (usually at the end, after channel)
    reference = None
    ref_match = re.search(r"(?:Ref\.|Reference|REF)\s*:?\s*(\S+)", line, re.IGNORECASE)
    if ref_match:
        reference = ref_match.group(1)

    return Transaction(
        date=txn_date,
        time=txn_time,
        description=description,
        channel=channel,
        withdrawal=withdrawal,
        deposit=deposit,
        balance=balance,
        reference=reference,
    )


# =============================================================================
# BBL (Bangkok Bank) specific parsing functions
# =============================================================================


def extract_account_info_bbl(
    text: str,
) -> tuple[str | None, str | None, date | None, date | None, str | None, str | None]:
    """Extract account info from BBL PDF header text.

    Supports both Thai and English formats:
    - Branch: "0369 KUMPHAWAPI BRANCH" or "0369 สาขากุมภวาปี"
    - Account: "Account No. 369-4-58959-3" or "เลขที่บัญชี/Account No. 369-4-58959-3"
    - Name: "Name MR NUTCHANON" or "ชื่อ/Name นาย ณัฐชนน"
    - Currency: "Currency THB" or "สกุลเงิน/Currency THB"
    - Period: "Statement Period 01/11/2025 - 06/11/2025" or "รอบรายการบัญชี / Statement Period"

    Returns:
        (account_number, account_name, period_start, period_end, branch, currency)
    """
    account_number = None
    account_name = None
    period_start = None
    period_end = None
    branch = None
    currency = None

    # Branch patterns:
    # English: "0369 KUMPHAWAPI BRANCH"
    # Thai: "0369 สาขากุมภวาปี"
    branch_match = re.search(r"(\d{4}\s+[A-Z\s]+BRANCH)", text)
    if branch_match:
        branch = branch_match.group(1).strip()
    else:
        # Thai branch: 4 digits + สาขา + Thai text
        branch_match = re.search(r"(\d{4}\s+สาขา[ก-๙\s]+)", text)
        if branch_match:
            branch = branch_match.group(1).strip()

    # Account number pattern: XXX-X-XXXXX-X
    acc_match = re.search(r"(\d{3}-\d-\d{5}-\d)", text)
    if acc_match:
        account_number = acc_match.group(1)

    # Currency pattern: "Currency THB" or "สกุลเงิน/Currency THB"
    currency_match = re.search(r"(?:Currency|สกุลเงิน/Currency)\s+([A-Z]{3})", text)
    if currency_match:
        currency = currency_match.group(1)
    else:
        currency = "THB"  # Default for Thai banks

    # Period patterns:
    # English: "Statement Period DD/MM/YYYY - DD/MM/YYYY"
    # Thai: "รอบรายการบัญชี / Statement Period DD/MM/YYYY - DD/MM/YYYY"
    period_match = re.search(
        r"(?:Statement Period|รอบรายการบัญชี\s*/\s*Statement Period)\s+(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
        text,
    )
    if period_match:
        start_parts = period_match.group(1).split("/")
        end_parts = period_match.group(2).split("/")
        period_start = date(int(start_parts[2]), int(start_parts[1]), int(start_parts[0]))
        period_end = date(int(end_parts[2]), int(end_parts[1]), int(end_parts[0]))

    # Account name patterns:
    # English: "Name MR/MRS/MS NAME"
    # Thai: "ชื่อ/Name นาย/นาง/นางสาว NAME"
    # Try English first
    name_match = re.search(r"Name\s+((?:MR|MRS|MS)\s+[A-Z\s]+?)(?:\s+เลขที่|Account|\n)", text)
    if name_match:
        account_name = name_match.group(1).strip()
    else:
        # Try Thai: ชื่อ/Name followed by Thai honorific + name
        name_match = re.search(r"ชื่อ/Name\s+((?:นาย|นาง|นางสาว)\s+[ก-๙\s]+?)(?:\s+เลขที่)", text)
        if name_match:
            account_name = name_match.group(1).strip()

    return account_number, account_name, period_start, period_end, branch, currency


def extract_balances_bbl(text: str) -> tuple[Decimal | None, Decimal | None]:
    """Extract opening and closing balances from BBL statement.

    BBL format:
    - Opening: "B/F" line with balance
    - Closing: Last transaction balance (second-to-last amount on line before channel)

    Returns:
        (opening_balance, closing_balance)
    """
    opening = None
    closing = None

    # B/F (Brought Forward) = Beginning Balance
    bf_match = re.search(r"B/F\s+([\d,]+\.\d{2})", text)
    if bf_match:
        opening = parse_amount(bf_match.group(1))

    # Find all transaction lines and get the balance (second-to-last column before channel)
    # BBL format: DD/MM/YY DESCRIPTION [withdrawal] [deposit] balance channel
    # We need to find all amounts on each line and take the last amount as balance
    lines = text.split("\n")
    last_balance = None

    for line in lines:
        # Check if line starts with a date
        if re.match(r"^\d{2}/\d{2}/\d{2}\s+", line) and "B/F" not in line:
            # Find all amounts on this line
            amounts = re.findall(r"([\d,]+\.\d{2})", line)
            if len(amounts) >= 2:
                # Last amount is the balance
                last_balance = parse_amount(amounts[-1])
            elif len(amounts) == 1:
                last_balance = parse_amount(amounts[0])

    if last_balance is not None:
        closing = last_balance

    return opening, closing


def parse_transaction_line_bbl(line: str) -> Transaction | None:
    """Parse a BBL transaction line.

    BBL format: DD/MM/YY DESCRIPTION [CHQ.NO] WITHDRAWAL DEPOSIT BALANCE VIA
    Example: "01/11/25 TRF TO OTH BK 48,755.00 782,344.60 mPhone"
    Example with branch: "04/11/25 CASH DEP NBK 10,000.00 688,797.52 BR0369 KUMPHAWAPI"

    Note: BBL transactions do NOT have time, and amounts can be blank.

    Args:
        line: Transaction line text

    Returns:
        Transaction object or None
    """
    # Pattern: DD/MM/YY at start
    date_pattern = re.compile(r"^(\d{2}/\d{2}/\d{2})\s+")
    match = date_pattern.match(line)
    if not match:
        return None

    date_str = match.group(1)

    # Skip B/F (Beginning Balance) line
    if "B/F" in line:
        return None

    # Parse date (DD/MM/YY format)
    try:
        day, month, year = date_str.split("/")
        full_year = 2000 + int(year)
        txn_date = date(full_year, int(month), int(day))
    except Exception:
        return None

    # BBL transactions don't have time
    txn_time = None

    # Find all amounts (numbers with commas and decimals)
    amount_pattern = re.compile(r"([\d,]+\.\d{2})")
    amounts = amount_pattern.findall(line)

    if not amounts:
        return None

    # Extract description - everything between date and first amount
    desc_match = re.search(r"^\d{2}/\d{2}/\d{2}\s+(.+?)(?:\d[\d,]*\.\d{2})", line)
    description = desc_match.group(1).strip() if desc_match else ""

    # Extract check number if present (between description and amounts)
    # Check numbers are typically numeric sequences in the description area
    check_number = None
    # BBL check numbers would appear before the amounts - currently not in sample data

    # Determine transaction type and amounts
    withdrawal = None
    deposit = None
    balance = None

    # Use keyword lists
    withdrawal_keywords = get_withdrawal_keywords()
    deposit_keywords = get_deposit_keywords()

    is_withdrawal = any(kw in line for kw in withdrawal_keywords) and not any(
        kw in line for kw in deposit_keywords
    )
    is_deposit = any(kw in line for kw in deposit_keywords)

    # BBL format: amounts are in order [withdrawal] [deposit] balance
    # But typically only one of withdrawal/deposit is present
    if len(amounts) >= 2:
        if is_withdrawal:
            withdrawal = parse_amount(amounts[0])
            balance = parse_amount(amounts[-1])
        elif is_deposit:
            deposit = parse_amount(amounts[0])
            balance = parse_amount(amounts[-1])
        else:
            # Default: assume withdrawal if can't determine
            balance = parse_amount(amounts[-1])
            withdrawal = parse_amount(amounts[0])
    elif len(amounts) == 1:
        balance = parse_amount(amounts[0])

    if balance is None:
        return None

    # Extract channel (Via) - can be mPhone, Gtway, or BR#### with branch name
    channel = None

    # Check for branch channel with name (e.g., "BR0369 KUMPHAWAPI")
    branch_channel_match = re.search(r"(BR\d{4})\s+([A-Z]+)", line)
    if branch_channel_match:
        channel = f"{branch_channel_match.group(1)} {branch_channel_match.group(2)}"
    else:
        # Check for simple branch channel (BR####)
        branch_match = re.search(r"\b(BR\d{4})\b", line)
        if branch_match:
            channel = branch_match.group(1)
        else:
            # Check for other channel keywords
            channel_keywords = get_channel_keywords()
            for kw in channel_keywords:
                if kw.lower() in line.lower():
                    channel = kw
                    break

    return Transaction(
        date=txn_date,
        time=txn_time,
        description=description,
        channel=channel,
        withdrawal=withdrawal,
        deposit=deposit,
        balance=balance,
        reference=None,
        check_number=check_number,
    )


# =============================================================================
# SCB (Siam Commercial Bank) specific parsing functions
# =============================================================================


def extract_account_info_scb(
    text: str,
) -> tuple[str | None, str | None, date | None, date | None, str | None, str | None]:
    """Extract account info from SCB PDF header text.

    SCB format:
    - Branch: "UDON THANI BRANCH"
    - Account: "423-044803-0"
    - Name: "นาย ณัฐชนน นินยวี"
    - Period: "01/04/2024 - 30/04/2024"

    Returns:
        (account_number, account_name, period_start, period_end, branch, currency)
    """
    account_number = None
    account_name = None
    period_start = None
    period_end = None
    branch = None
    currency = "THB"

    # Branch pattern: "XXX BRANCH" but not the bank name header
    branch_match = re.search(r"^([A-Z][A-Z ]+BRANCH)$", text, re.MULTILINE)
    if branch_match and "COMMERCIAL" not in branch_match.group(1):
        branch = branch_match.group(1).strip()

    # Account number pattern: XXX-XXXXXX-X (SCB format)
    acc_match = re.search(r"(\d{3}-\d{6}-\d)", text)
    if acc_match:
        account_number = acc_match.group(1)

    # Period pattern: DD/MM/YYYY - DD/MM/YYYY
    period_match = re.search(
        r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
        text,
    )
    if period_match:
        start_parts = period_match.group(1).split("/")
        end_parts = period_match.group(2).split("/")
        period_start = date(int(start_parts[2]), int(start_parts[1]), int(start_parts[0]))
        period_end = date(int(end_parts[2]), int(end_parts[1]), int(end_parts[0]))

    # Account name - Thai honorific + name before account number
    name_match = re.search(r"((?:นาย|นาง|นางสาว)\s+[ก-๙\s]+?)\s+\d{3}-\d{6}-\d", text)
    if name_match:
        account_name = name_match.group(1).strip()

    return account_number, account_name, period_start, period_end, branch, currency


def extract_balances_scb(text: str) -> tuple[Decimal | None, Decimal | None]:
    """Extract opening and closing balances from SCB statement.

    SCB format:
    - Opening: "ยอดเงินคงเหลือยกมา (BALANCE BROUGHT FORWARD) XX,XXX.XX"
    - Closing: Last transaction balance

    Returns:
        (opening_balance, closing_balance)
    """
    opening = None
    closing = None

    # Opening balance - BALANCE BROUGHT FORWARD
    bf_match = re.search(r"BALANCE BROUGHT FORWARD\)?\s*([\d,]+\.\d{2})", text)
    if bf_match:
        opening = parse_amount(bf_match.group(1))

    # Closing balance - find last transaction balance
    # SCB transactions have format: DD/MM/YY HH:MM X1/X2 Channel Amount Balance Description
    txn_pattern = re.compile(
        r"^\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}\s+X[12]\s+\w+\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})",
        re.MULTILINE,
    )
    matches = txn_pattern.findall(text)
    if matches:
        closing = parse_amount(matches[-1])

    return opening, closing


def parse_transaction_line_scb(line: str) -> Transaction | None:
    """Parse an SCB transaction line.

    SCB format: DD/MM/YY HH:MM Code Channel Amount Balance Description
    Code: X1=Credit (deposit), X2=Debit (withdrawal)

    Example: "01/04/24 19:20 X2 ENET 3,470.00 42,072.00 PromptPay x9119 นาย วรพงษ์"

    Args:
        line: Transaction line text

    Returns:
        Transaction object or None
    """
    # Pattern: DD/MM/YY HH:MM X1/X2 Channel Amount Balance Description
    pattern = re.compile(
        r"^(\d{2}/\d{2}/\d{2})\s+"  # Date
        r"(\d{2}:\d{2})\s+"  # Time
        r"(X[12])\s+"  # Code (X1=credit, X2=debit)
        r"(\w+)\s+"  # Channel
        r"([\d,]+\.\d{2})\s+"  # Amount
        r"([\d,]+\.\d{2})\s+"  # Balance
        r"(.+)$"  # Description
    )

    match = pattern.match(line)
    if not match:
        return None

    date_str = match.group(1)
    time_str = match.group(2)
    code = match.group(3)
    channel = match.group(4)
    amount_str = match.group(5)
    balance_str = match.group(6)
    description = match.group(7).strip()

    # Parse date (DD/MM/YY format)
    try:
        day, month, year = date_str.split("/")
        full_year = 2000 + int(year)
        txn_date = date(full_year, int(month), int(day))
    except Exception:
        return None

    # Parse time
    try:
        hour, minute = time_str.split(":")
        txn_time = time(int(hour), int(minute))
    except Exception:
        txn_time = None

    amount = parse_amount(amount_str)
    balance = parse_amount(balance_str)

    # X1 = Credit (deposit), X2 = Debit (withdrawal)
    if code == "X1":
        deposit = amount
        withdrawal = None
    else:  # X2
        withdrawal = amount
        deposit = None

    return Transaction(
        date=txn_date,
        time=txn_time,
        description=description,
        channel=channel,
        withdrawal=withdrawal,
        deposit=deposit,
        balance=balance,
        reference=None,
        check_number=None,
    )


def parse_pdf(
    pdf_path: Path | str,
    password: str = DEFAULT_PASSWORD,
) -> Statement:
    """Parse a bank PDF statement (KBank, BBL, or SCB).

    Automatically detects bank type and uses appropriate parser.

    Args:
        pdf_path: Path to PDF file
        password: PDF password for decryption

    Returns:
        Statement object with all extracted data
    """
    pdf_path = Path(pdf_path)

    # Decrypt PDF
    try:
        pdf_bytes = decrypt_pdf(pdf_path, password)
        pdf_file = io.BytesIO(pdf_bytes)
    except pikepdf.PasswordError:
        # Try without password (might be unencrypted)
        pdf_file = str(pdf_path)

    # Extract all text first for header info
    all_text = ""
    transactions: list[Transaction] = []

    # Initialize bank-specific fields
    branch = None
    currency = "THB"

    with pdfplumber.open(pdf_file) as pdf:
        # Get full text first for bank detection
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        # Detect bank type
        bank_type = detect_bank_type(full_text)

        # Get header info from first page
        if pdf.pages:
            first_page_text = pdf.pages[0].extract_text() or ""
            all_text = first_page_text

        # Extract account info based on bank type
        if bank_type == BANK_BBL:
            (
                account_number,
                account_name,
                period_start,
                period_end,
                branch,
                currency,
            ) = extract_account_info_bbl(all_text)
            opening_balance, closing_balance = extract_balances_bbl(full_text)
        elif bank_type == BANK_SCB:
            (
                account_number,
                account_name,
                period_start,
                period_end,
                branch,
                currency,
            ) = extract_account_info_scb(all_text)
            opening_balance, closing_balance = extract_balances_scb(full_text)
        else:
            account_number, account_name, period_start, period_end = extract_account_info(all_text)
            opening_balance, closing_balance = extract_balances(full_text)

        # Detect language
        language = detect_pdf_language(full_text)

        # Parse transactions from all pages using bank-specific parser
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            lines = page_text.split("\n")

            for line in lines:
                if bank_type == BANK_BBL:
                    txn = parse_transaction_line_bbl(line)
                elif bank_type == BANK_SCB:
                    txn = parse_transaction_line_scb(line)
                else:
                    txn = parse_transaction_line(line)
                if txn:
                    transactions.append(txn)

    # Create statement
    stmt_account = account_number or "UNKNOWN"
    stmt_period_start = period_start or date.today()
    stmt_period_end = period_end or date.today()

    return Statement(
        account_number=stmt_account,
        account_name=account_name,
        statement_period_start=stmt_period_start,
        statement_period_end=stmt_period_end,
        opening_balance=opening_balance or Decimal("0"),
        closing_balance=closing_balance or Decimal("0"),
        transactions=transactions,
        source_pdf=str(pdf_path),
        language=language,
        bank=bank_type,
        branch=branch,
        currency=currency or "THB",
    )


def parse_all_pdfs(
    download_dir: Path | str,
    password: str = DEFAULT_PASSWORD,
) -> list[Statement]:
    """Parse all PDFs in a directory.

    Args:
        download_dir: Directory containing PDFs
        password: PDF password

    Returns:
        List of Statement objects
    """
    download_dir = Path(download_dir)
    statements: list[Statement] = []

    # Match both .pdf and .PDF extensions
    pdf_files = list(download_dir.glob("*.pdf")) + list(download_dir.glob("*.PDF"))

    for pdf_path in pdf_files:
        try:
            statement = parse_pdf(pdf_path, password)
            statements.append(statement)
        except Exception:
            # Skip files that can't be parsed
            pass

    return statements
