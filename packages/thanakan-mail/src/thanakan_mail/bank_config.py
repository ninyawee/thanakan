"""Bank-specific email configurations and filters."""

from dataclasses import dataclass

from .models import EmailAttachment


@dataclass(frozen=True)
class BankEmailConfig:
    """Configuration for a specific bank's emails."""

    bank_code: str  # "kbank", "bbl", "scb"
    sender_email: str
    subject_filter: str | None = None
    filename_patterns: tuple[str, ...] = ()

    def build_gmail_query(
        self,
        since: str | None = None,
        until: str | None = None,
    ) -> str:
        """Build Gmail search query for this bank.

        Args:
            since: Emails newer than this duration (e.g., "30d", "2w", "3m", "1y")
            until: Emails older than this duration (e.g., "7d", "1w")

        Duration format:
            - Nd = N days (e.g., 30d = last 30 days)
            - Nw = N weeks (e.g., 2w = last 2 weeks)
            - Nm = N months (e.g., 3m = last 3 months)
            - Ny = N years (e.g., 1y = last year)
        """
        query = f"from:{self.sender_email} has:attachment"
        if self.subject_filter:
            query += f" subject:{self.subject_filter}"
        if since is not None:
            query += f" newer_than:{since}"
        if until is not None:
            query += f" older_than:{until}"
        return query

    def matches_filename(self, filename: str) -> bool:
        """Check if filename matches bank's statement patterns."""
        filename_lower = filename.lower()
        return any(
            filename_lower.startswith(pattern.lower())
            for pattern in self.filename_patterns
        )


# Bank configurations
KBANK_CONFIG = BankEmailConfig(
    bank_code="kbank",
    sender_email="K-ElectronicDocument@kasikornbank.com",
    subject_filter=None,
    filename_patterns=("stm_",),
)

BBL_CONFIG = BankEmailConfig(
    bank_code="bbl",
    sender_email="BualuangmBanking@bangkokbank.com",
    subject_filter="รายการเดินบัญชี",
    filename_patterns=("statement of ", "statement_of_"),
)

SCB_CONFIG = BankEmailConfig(
    bank_code="scb",
    sender_email="scbeasynet@scb.co.th",
    subject_filter="account statement",
    filename_patterns=("acctst_",),
)

BANK_CONFIGS: dict[str, BankEmailConfig] = {
    "kbank": KBANK_CONFIG,
    "bbl": BBL_CONFIG,
    "scb": SCB_CONFIG,
}


def is_statement_pdf(attachment: EmailAttachment, config: BankEmailConfig) -> bool:
    """Check if attachment is a PDF statement matching bank patterns."""
    # Must be PDF (application/pdf or octet-stream with .pdf extension)
    is_pdf = (
        attachment.mime_type == "application/pdf"
        or (
            attachment.mime_type == "application/octet-stream"
            and attachment.filename.lower().endswith(".pdf")
        )
    )

    if not is_pdf:
        return False

    return config.matches_filename(attachment.filename)
