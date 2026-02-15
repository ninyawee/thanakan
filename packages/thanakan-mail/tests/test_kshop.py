"""Tests for KShop email parsing."""

from decimal import Decimal

import pytest

from thanakan_mail.kshop import KShopSummary, KShopParseError, parse_kshop_email
from thanakan_mail.models import EmailMessage


# =============================================================================
# Fixtures
# =============================================================================

SAMPLE_BODY = """\
เรียน ร้านค้า K SHOP ร้านตัวอย่าง

ธนาคารกสิกรไทยได้ทำการสรุปยอดประจำวันสำหรับรายการของร้านค้า K SHOP (ร้านตัวอย่าง) เรียบร้อยแล้ว โดยมีรายละเอียดดังต่อไปนี้
รหัสร้านค้า : KB000000000001
ยอดเงินจำนวน(บาท) : 4,250.00
นำเข้าบัญชี : xxx-x-x0000-x (นาย ชื่อ นามสกุล)

จึงเรียนมาเพื่อโปรดพิจารณา
บมจ. ธนาคารกสิกรไทย
"""


def _make_message(
    body: str = SAMPLE_BODY,
    subject: str = "เรียน ร้านค้า K SHOP ร้านตัวอย่าง",
    date: str = "Sat, 15 Feb 2026 10:30:00 +0700",
    message_id: str = "msg001",
) -> EmailMessage:
    return EmailMessage(
        message_id=message_id,
        subject=subject,
        sender="KSHOP <KPLUSSHOP@kasikornbank.com>",
        date=date,
        body=body,
    )


# =============================================================================
# Tests for parse_kshop_email
# =============================================================================


class TestParseKShopEmail:
    """Tests for parse_kshop_email()."""

    def test_parses_standard_email(self):
        result = parse_kshop_email(_make_message())

        assert result.store_id == "KB000000000001"
        assert result.store_name == "ร้านตัวอย่าง"
        assert result.daily_amount == Decimal("4250.00")
        assert result.account_number == "xxx-x-x0000-x"
        assert result.account_name == "นาย ชื่อ นามสกุล"
        assert result.email_id == "msg001"

    def test_extracts_store_name_from_body_parentheses(self):
        result = parse_kshop_email(_make_message())
        assert result.store_name == "ร้านตัวอย่าง"

    def test_extracts_store_name_from_subject_fallback(self):
        body = SAMPLE_BODY.replace(
            "ร้านค้า K SHOP (ร้านตัวอย่าง)", "ร้านค้า K SHOP"
        )
        result = parse_kshop_email(_make_message(body=body))
        assert result.store_name == "ร้านตัวอย่าง"

    def test_handles_amount_without_comma(self):
        body = SAMPLE_BODY.replace("4,250.00", "900.00")
        result = parse_kshop_email(_make_message(body=body))
        assert result.daily_amount == Decimal("900.00")

    def test_handles_large_amount(self):
        body = SAMPLE_BODY.replace("4,250.00", "1,234,567.89")
        result = parse_kshop_email(_make_message(body=body))
        assert result.daily_amount == Decimal("1234567.89")

    def test_handles_integer_amount(self):
        body = SAMPLE_BODY.replace("4,250.00", "5000")
        result = parse_kshop_email(_make_message(body=body))
        assert result.daily_amount == Decimal("5000")

    def test_preserves_email_metadata(self):
        result = parse_kshop_email(
            _make_message(
                message_id="abc123",
                date="Mon, 10 Feb 2026 08:00:00 +0700",
            )
        )
        assert result.email_id == "abc123"
        assert result.email_date == "Mon, 10 Feb 2026 08:00:00 +0700"

    def test_handles_different_account_format(self):
        body = SAMPLE_BODY.replace("xxx-x-x0000-x", "123-4-56789-0")
        result = parse_kshop_email(_make_message(body=body))
        assert result.account_number == "123-4-56789-0"

    def test_handles_no_account_name(self):
        body = SAMPLE_BODY.replace(
            "นำเข้าบัญชี : xxx-x-x0000-x (นาย ชื่อ นามสกุล)",
            "นำเข้าบัญชี : xxx-x-x0000-x",
        )
        result = parse_kshop_email(_make_message(body=body))
        assert result.account_number == "xxx-x-x0000-x"
        assert result.account_name == ""


class TestParseKShopEmailErrors:
    """Tests for parse_kshop_email() error cases."""

    def test_raises_on_empty_body(self):
        with pytest.raises(KShopParseError, match="body is empty"):
            parse_kshop_email(_make_message(body=""))

    def test_raises_on_missing_store_id(self):
        body = SAMPLE_BODY.replace("KB000000000001", "XXXXXXXXX")
        with pytest.raises(KShopParseError, match="store ID"):
            parse_kshop_email(_make_message(body=body))

    def test_raises_on_missing_amount(self):
        body = SAMPLE_BODY.replace("ยอดเงินจำนวน(บาท) : 4,250.00", "")
        with pytest.raises(KShopParseError, match="daily amount"):
            parse_kshop_email(_make_message(body=body))

    def test_raises_on_missing_account(self):
        body = SAMPLE_BODY.replace(
            "นำเข้าบัญชี : xxx-x-x0000-x (นาย ชื่อ นามสกุล)", ""
        )
        with pytest.raises(KShopParseError, match="account number"):
            parse_kshop_email(_make_message(body=body))

    def test_raises_on_invalid_amount(self):
        body = SAMPLE_BODY.replace("4,250.00", "abc")
        with pytest.raises(KShopParseError, match="daily amount"):
            parse_kshop_email(_make_message(body=body))


# =============================================================================
# Tests for KShopSummary model
# =============================================================================


class TestKShopSummaryModel:
    """Tests for KShopSummary Pydantic model."""

    def test_serializes_to_json(self):
        summary = KShopSummary(
            email_id="msg001",
            email_date="Sat, 15 Feb 2026 10:30:00 +0700",
            store_name="ร้านตัวอย่าง",
            store_id="KB000000000001",
            daily_amount=Decimal("4250.00"),
            account_number="xxx-x-x0000-x",
            account_name="นาย ชื่อ นามสกุล",
        )
        data = summary.model_dump(mode="json")

        assert data["store_id"] == "KB000000000001"
        assert data["daily_amount"] == "4250.00"
        assert data["account_name"] == "นาย ชื่อ นามสกุล"

    def test_account_name_defaults_empty(self):
        summary = KShopSummary(
            email_id="x",
            email_date="x",
            store_name="x",
            store_id="KB1",
            daily_amount=Decimal("0"),
            account_number="x",
        )
        assert summary.account_name == ""
