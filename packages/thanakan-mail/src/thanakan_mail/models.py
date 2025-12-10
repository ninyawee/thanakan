"""Pydantic models for email downloading."""


from pydantic import BaseModel, Field


class EmailAttachment(BaseModel):
    """Attachment metadata."""

    attachment_id: str
    filename: str
    mime_type: str
    size_bytes: int | None = None


class EmailMessage(BaseModel):
    """Email message with metadata."""

    message_id: str
    thread_id: str | None = None
    subject: str = ""
    sender: str = ""
    date: str = ""
    attachments: list[EmailAttachment] = Field(default_factory=list)


class DownloadResult(BaseModel):
    """Result of downloading attachments from one email."""

    message: EmailMessage
    downloaded_files: list[str] = Field(default_factory=list)
    skipped_attachments: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class EmailMetadata(BaseModel):
    """Metadata for a downloaded email (for JSON persistence)."""

    email_id: str
    thread_id: str | None = None
    date: str
    subject: str
    pdf_filenames: list[str] = Field(default_factory=list)
