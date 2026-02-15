"""Email provider abstraction and Gmail implementation."""

from __future__ import annotations

import base64
import binascii
import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from .models import EmailAttachment, EmailMessage

# Gmail API scope - read only
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@runtime_checkable
class EmailProvider(Protocol):
    """Protocol for email provider implementations.

    Defines the contract for email providers (Gmail, Outlook, etc.).
    Uses Protocol for structural subtyping - more Pythonic and flexible.
    """

    def authenticate(self) -> None:
        """Authenticate with the email provider."""
        ...

    def search_messages(self, query: str, max_results: int = 100) -> list[EmailMessage]:
        """Search for messages matching the query."""
        ...

    def get_message_details(self, message_id: str) -> EmailMessage:
        """Fetch full message details including attachments."""
        ...

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download a specific attachment."""
        ...


class GmailProvider:
    """Gmail implementation using Google API client.

    Implements the EmailProvider protocol.

    Note: This class is not thread-safe. For concurrent use, create
    separate instances per thread.
    """

    def __init__(
        self,
        client_secret_path: Path | str | None = None,
        token_path: Path | str | None = None,
    ):
        """Initialize Gmail provider.

        Args:
            client_secret_path: Path to OAuth client_secret.json
                (default: env GMAIL_CLIENT_SECRET)
            token_path: Path to store OAuth token
                (default: env GMAIL_TOKEN_PATH or ~/.thanakan/gmail_token.json)
        """
        # Resolve client secret path
        if client_secret_path is None:
            client_secret_env = os.getenv("GMAIL_CLIENT_SECRET")
            if not client_secret_env:
                raise ValueError(
                    "GMAIL_CLIENT_SECRET environment variable required. "
                    "Download client_secret.json from Google Cloud Console."
                )
            client_secret_path = Path(client_secret_env)
        else:
            client_secret_path = Path(client_secret_path)

        # Resolve token path
        if token_path is None:
            token_path_env = os.getenv("GMAIL_TOKEN_PATH")
            if token_path_env:
                token_path = Path(token_path_env)
            else:
                token_path = Path.home() / ".thanakan" / "gmail_token.json"
        else:
            token_path = Path(token_path)

        self.client_secret_path = client_secret_path
        self.token_path = token_path
        self._service: Resource | None = None

    @property
    def service(self) -> Resource:
        """Get authenticated Gmail service (lazy initialization)."""
        if self._service is None:
            self.authenticate()
        return self._service

    def authenticate(self) -> None:
        """Authenticate with Gmail using OAuth 2.0."""
        creds: Credentials | None = None

        # Load existing token
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_path),
                GMAIL_SCOPES,
            )

        # Refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.client_secret_path.exists():
                    raise FileNotFoundError(
                        f"Gmail client secret not found at {self.client_secret_path}. "
                        f"Download from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secret_path),
                    GMAIL_SCOPES,
                )
                creds = flow.run_local_server(
                    port=8080,
                    authorization_prompt_message="Visit: {url}",
                    success_message="Authentication successful! Close this window.",
                    open_browser=True,
                )

            # Save credentials
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self.token_path.write_text(creds.to_json())
            except OSError as e:
                raise OSError(f"Failed to save OAuth token to {self.token_path}: {e}") from e

        self._service = build("gmail", "v1", credentials=creds)

    def search_messages(self, query: str, max_results: int = 100) -> list[EmailMessage]:
        """Search for messages using Gmail query syntax."""
        messages: list[dict] = []
        page_token: str | None = None

        while len(messages) < max_results:
            result = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=min(max_results - len(messages), 100),
                    pageToken=page_token,
                )
                .execute()
            )

            if "messages" in result:
                messages.extend(result["messages"])

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        # Return basic metadata only (details fetched separately)
        return [
            EmailMessage(
                message_id=msg["id"],
                thread_id=msg.get("threadId"),
            )
            for msg in messages[:max_results]
        ]

    def get_message_details(self, message_id: str) -> EmailMessage:
        """Fetch full message details including attachments."""
        msg = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        # Extract headers
        headers = msg.get("payload", {}).get("headers", [])
        subject = self._get_header(headers, "Subject")
        sender = self._get_header(headers, "From")
        date = self._get_header(headers, "Date")

        # Extract attachments and body
        payload = msg.get("payload", {})
        attachments = self._extract_attachments(payload)
        body = self._extract_body_text(payload)

        return EmailMessage(
            message_id=message_id,
            thread_id=msg.get("threadId"),
            subject=subject,
            sender=sender,
            date=date,
            body=body,
            attachments=attachments,
        )

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download attachment bytes."""
        attachment = (
            self.service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )

        try:
            data = attachment.get("data")
            if not data:
                raise ValueError(f"Attachment {attachment_id} has no data")
            return base64.urlsafe_b64decode(data)
        except (binascii.Error, ValueError) as e:
            raise ValueError(
                f"Failed to decode attachment {attachment_id}: {e}"
            ) from e

    def get_profile(self) -> dict:
        """Get user profile (for testing authentication)."""
        return self.service.users().getProfile(userId="me").execute()

    @staticmethod
    def _get_header(headers: list[dict], name: str) -> str:
        """Extract header value by name."""
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    def _extract_body_text(self, payload: dict) -> str:
        """Extract plain text body from email payload."""
        # Single-part message
        if payload.get("mimeType") == "text/plain":
            body_data = payload.get("body", {}).get("data")
            if body_data:
                try:
                    return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
                except (binascii.Error, ValueError):
                    return ""

        # Multipart message - find text/plain part
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                body_data = part.get("body", {}).get("data")
                if body_data:
                    try:
                        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
                    except (binascii.Error, ValueError):
                        continue
            # Recurse into nested parts (e.g., multipart/alternative inside multipart/mixed)
            if "parts" in part:
                text = self._extract_body_text(part)
                if text:
                    return text

        return ""

    def _extract_attachments(self, payload: dict) -> list[EmailAttachment]:
        """Recursively extract attachment metadata from payload."""
        attachments: list[EmailAttachment] = []

        def process_parts(parts: list[dict]) -> None:
            for part in parts:
                filename = part.get("filename", "")
                mime_type = part.get("mimeType", "")
                body = part.get("body", {})
                attachment_id = body.get("attachmentId")

                if attachment_id and filename:
                    attachments.append(
                        EmailAttachment(
                            attachment_id=attachment_id,
                            filename=filename,
                            mime_type=mime_type,
                            size_bytes=body.get("size"),
                        )
                    )

                # Recurse into nested parts
                if "parts" in part:
                    process_parts(part["parts"])

        if "parts" in payload:
            process_parts(payload["parts"])

        return attachments
