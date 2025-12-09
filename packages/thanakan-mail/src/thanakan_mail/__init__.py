"""Download Thai bank PDF statements from email."""

from .models import (
    EmailAttachment,
    EmailMessage,
    EmailMetadata,
    DownloadResult,
)
from .bank_config import (
    BankEmailConfig,
    KBANK_CONFIG,
    BBL_CONFIG,
    SCB_CONFIG,
    BANK_CONFIGS,
)
from .provider import (
    EmailProvider,
    GmailProvider,
)
from .downloader import (
    StatementDownloader,
    download_bank_statements,
    results_to_metadata,
    save_metadata,
)
from .unlock import (
    unlock_pdf,
    unlock_pdfs,
    is_pdf_encrypted,
    get_saved_password,
    save_password,
    clear_saved_password,
)

__all__ = [
    "EmailAttachment",
    "EmailMessage",
    "EmailMetadata",
    "DownloadResult",
    "BankEmailConfig",
    "KBANK_CONFIG",
    "BBL_CONFIG",
    "SCB_CONFIG",
    "BANK_CONFIGS",
    "EmailProvider",
    "GmailProvider",
    "StatementDownloader",
    "download_bank_statements",
    "results_to_metadata",
    "save_metadata",
    "unlock_pdf",
    "unlock_pdfs",
    "is_pdf_encrypted",
    "get_saved_password",
    "save_password",
    "clear_saved_password",
]
