"""High-level facade for downloading bank statement PDFs from email."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from .bank_config import BankEmailConfig, BANK_CONFIGS, is_statement_pdf
from .models import DownloadResult, EmailMetadata

if TYPE_CHECKING:
    from .provider import EmailProvider


class StatementDownloader:
    """Downloads bank statement PDFs from email.

    Orchestrates: email provider + bank config + filtering.
    """

    def __init__(
        self,
        provider: EmailProvider,
        bank_config: BankEmailConfig,
        download_dir: Path | str,
    ):
        """Initialize downloader.

        Args:
            provider: Email provider implementation (GmailProvider, etc.)
            bank_config: Bank-specific configuration
            download_dir: Directory to save downloaded PDFs
        """
        self.provider = provider
        self.bank_config = bank_config
        self.download_dir = Path(download_dir)

    def download_statements(
        self,
        max_emails: int = 100,
        since: str | None = None,
        until: str | None = None,
        verbose: bool = False,
    ) -> list[DownloadResult]:
        """Download all statement PDFs for this bank.

        Args:
            max_emails: Maximum emails to process
            since: Emails newer than this duration (e.g., "30d", "2w", "3m", "1y")
            until: Emails older than this duration (e.g., "7d", "1w")
            verbose: Print progress messages

        Returns:
            List of download results (one per email)
        """
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Search for emails
        if verbose:
            print(f"Searching for {self.bank_config.bank_code.upper()} emails...")

        query = self.bank_config.build_gmail_query(since=since, until=until)
        messages = self.provider.search_messages(query, max_results=max_emails)

        if verbose:
            print(f"Found {len(messages)} emails")

        # Process each email
        results: list[DownloadResult] = []

        for i, msg_preview in enumerate(messages, 1):
            if verbose:
                print(f"\n[{i}/{len(messages)}] Processing {msg_preview.message_id}...")

            result = self._process_message(msg_preview.message_id, verbose=verbose)
            results.append(result)

        if verbose:
            total_pdfs = sum(len(r.downloaded_files) for r in results)
            print(f"\nDownloaded {total_pdfs} PDFs from {len(results)} emails")

        return results

    def _process_message(self, message_id: str, verbose: bool = False) -> DownloadResult:
        """Process a single email message."""
        # Get full message details
        message = self.provider.get_message_details(message_id)

        if verbose:
            print(f"  Subject: {message.subject}")
            print(f"  Date: {message.date}")

        result = DownloadResult(message=message)

        # Process each attachment
        for attachment in message.attachments:
            if not is_statement_pdf(attachment, self.bank_config):
                result.skipped_attachments.append(attachment.filename)
                if verbose:
                    print(f"  Skipped: {attachment.filename}")
                continue

            try:
                # Download attachment
                data = self.provider.download_attachment(
                    message_id,
                    attachment.attachment_id,
                )

                # Save to file (prefix with message_id to avoid collisions)
                filename = f"{message_id}_{attachment.filename}"
                file_path = self.download_dir / filename

                # Warn if file exists (will be overwritten)
                if file_path.exists() and verbose:
                    print(f"  Overwriting: {filename}")

                file_path.write_bytes(data)

                # Store relative filename for portability
                result.downloaded_files.append(filename)
                if verbose:
                    print(f"  Saved: {filename}")

            except Exception as e:
                error_msg = f"Failed to download {attachment.filename}: {e}"
                result.errors.append(error_msg)
                if verbose:
                    print(f"  Error: {error_msg}")

        return result


def download_bank_statements(
    bank: str,
    download_dir: str | Path,
    max_emails: int = 100,
    since: str | None = None,
    until: str | None = None,
    verbose: bool = False,
) -> list[DownloadResult]:
    """Convenience function to download statements for a bank.

    Args:
        bank: Bank code ("kbank", "bbl", "scb")
        download_dir: Directory to save PDFs
        max_emails: Maximum emails to process
        since: Emails newer than this duration (e.g., "30d", "2w", "3m", "1y")
        until: Emails older than this duration (e.g., "7d", "1w")
        verbose: Print progress

    Returns:
        List of download results
    """
    from .provider import GmailProvider

    if bank not in BANK_CONFIGS:
        raise ValueError(f"Unknown bank: {bank}. Available: {', '.join(BANK_CONFIGS.keys())}")

    provider = GmailProvider()
    bank_config = BANK_CONFIGS[bank]
    downloader = StatementDownloader(provider, bank_config, Path(download_dir))

    return downloader.download_statements(max_emails=max_emails, since=since, until=until, verbose=verbose)


def results_to_metadata(results: list[DownloadResult]) -> list[EmailMetadata]:
    """Convert download results to metadata format for JSON persistence."""
    return [
        EmailMetadata(
            email_id=r.message.message_id,
            thread_id=r.message.thread_id,
            date=r.message.date,
            subject=r.message.subject,
            pdf_filenames=r.downloaded_files,
        )
        for r in results
    ]


def save_metadata(
    results: list[DownloadResult],
    output_path: Path | str,
) -> None:
    """Save download results as metadata JSON."""
    metadata = results_to_metadata(results)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            [m.model_dump() for m in metadata],
            f,
            indent=2,
            default=str,
        )
