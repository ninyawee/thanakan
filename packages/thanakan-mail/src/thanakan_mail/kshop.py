"""KShop (K PLUS SHOP) daily summary email parsing.

Parses daily summary emails from KPLUSSHOP@kasikornbank.com to extract
store transaction data: store name, store ID, daily amount, and account number.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .models import EmailMessage

if TYPE_CHECKING:
    from .provider import EmailProvider

KSHOP_SENDER = "KPLUSSHOP@kasikornbank.com"


class KShopSummary(BaseModel):
    """Daily sales summary from a KShop email."""

    email_id: str
    email_date: str
    store_name: str
    store_id: str  # KB... format
    daily_amount: Decimal
    account_number: str  # May be partially masked (e.g., xxx-x-x0000-x)
    account_name: str = ""


class KShopParseError(Exception):
    """Raised when a KShop email cannot be parsed."""


def parse_kshop_email(message: EmailMessage) -> KShopSummary:
    """Parse a KShop daily summary email body.

    Args:
        message: Email message with body text populated.

    Returns:
        Parsed KShop daily summary.

    Raises:
        KShopParseError: If required fields cannot be extracted.
    """
    body = message.body
    if not body:
        raise KShopParseError("Email body is empty")

    # Store ID: รหัสร้านค้า : KB000000000000
    store_id_match = re.search(r"(KB\d+)", body)
    if not store_id_match:
        raise KShopParseError("Could not extract store ID (KB...)")
    store_id = store_id_match.group(1)

    # Store name: from subject "เรียน ร้านค้า K SHOP ชื่อร้าน"
    # or from body "ร้านค้า K SHOP (ชื่อร้าน)"
    store_name = ""
    # Try body first: "ร้านค้า K SHOP (NAME)"
    name_match = re.search(r"ร้านค้า\s+K\s*SHOP\s*\((.+?)\)", body)
    if name_match:
        store_name = name_match.group(1).strip()
    else:
        # Try subject: "เรียน ร้านค้า K SHOP NAME"
        subj_match = re.search(r"K\s*SHOP\s+(.+)", message.subject)
        if subj_match:
            store_name = subj_match.group(1).strip()

    # Daily amount: ยอดเงินจำนวน(บาท) : 4,250.00
    amount_match = re.search(
        r"ยอดเงินจำนวน\s*\(?\s*บาท\s*\)?\s*[:：]\s*([\d,]+\.?\d*)", body
    )
    if not amount_match:
        raise KShopParseError("Could not extract daily amount")
    try:
        daily_amount = Decimal(amount_match.group(1).replace(",", ""))
    except InvalidOperation as e:
        raise KShopParseError(f"Invalid amount format: {amount_match.group(1)}") from e

    # Account number: นำเข้าบัญชี : xxx-x-x0000-x (นาย ชื่อ นามสกุล)
    account_match = re.search(
        r"นำเข้าบัญชี\s*[:：]\s*([\dxX]+-[\dxX]+-[\dxX]+-[\dxX]+)", body
    )
    if not account_match:
        raise KShopParseError("Could not extract account number")
    account_number = account_match.group(1)

    # Account name: text in parentheses after account number
    account_name = ""
    acct_name_match = re.search(
        r"นำเข้าบัญชี\s*[:：]\s*[\dxX]+-[\dxX]+-[\dxX]+-[\dxX]+\s*\((.+?)\)", body
    )
    if acct_name_match:
        account_name = acct_name_match.group(1).strip()

    return KShopSummary(
        email_id=message.message_id,
        email_date=message.date,
        store_name=store_name,
        store_id=store_id,
        daily_amount=daily_amount,
        account_number=account_number,
        account_name=account_name,
    )


class KShopFetcher:
    """Fetches and parses KShop daily summary emails from Gmail."""

    def __init__(self, provider: EmailProvider):
        self.provider = provider

    def fetch_summaries(
        self,
        max_emails: int = 100,
        since: str | None = None,
        until: str | None = None,
        verbose: bool = False,
    ) -> list[KShopSummary]:
        """Fetch and parse KShop daily summaries.

        Args:
            max_emails: Maximum emails to process.
            since: Emails newer than this duration (e.g., "30d", "2w").
            until: Emails older than this duration (e.g., "7d", "1w").
            verbose: Print progress messages.

        Returns:
            List of parsed KShop daily summaries.
        """
        query = f"from:{KSHOP_SENDER}"
        if since:
            query += f" newer_than:{since}"
        if until:
            query += f" older_than:{until}"

        if verbose:
            print(f"Searching for KShop emails...")

        messages = self.provider.search_messages(query, max_results=max_emails)

        if verbose:
            print(f"Found {len(messages)} emails")

        summaries: list[KShopSummary] = []

        for i, msg_preview in enumerate(messages, 1):
            try:
                message = self.provider.get_message_details(msg_preview.message_id)

                if verbose:
                    print(f"[{i}/{len(messages)}] {message.subject} ({message.date})")

                summary = parse_kshop_email(message)
                summaries.append(summary)

                if verbose:
                    print(f"  {summary.store_id}: {summary.daily_amount} THB")

            except KShopParseError as e:
                if verbose:
                    print(f"  Parse error: {e}")
            except Exception as e:
                if verbose:
                    print(f"  Error: {e}")

        if verbose:
            print(f"\nParsed {len(summaries)} KShop summaries")

        return summaries


def fetch_kshop_summaries(
    max_emails: int = 100,
    since: str | None = None,
    until: str | None = None,
    verbose: bool = False,
) -> list[KShopSummary]:
    """Convenience function to fetch KShop summaries from Gmail.

    Args:
        max_emails: Maximum emails to process.
        since: Emails newer than this duration (e.g., "30d", "2w").
        until: Emails older than this duration (e.g., "7d", "1w").
        verbose: Print progress messages.

    Returns:
        List of KShop daily summaries.
    """
    from .provider import GmailProvider

    provider = GmailProvider()
    fetcher = KShopFetcher(provider)
    return fetcher.fetch_summaries(
        max_emails=max_emails,
        since=since,
        until=until,
        verbose=verbose,
    )


def save_kshop_json(
    summaries: list[KShopSummary],
    output_path: Path | str,
) -> None:
    """Save KShop summaries as JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [s.model_dump(mode="json") for s in summaries]
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
