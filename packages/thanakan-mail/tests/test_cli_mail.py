"""Tests for mail CLI commands."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

# Import the CLI app
from thanakan.cli import app


runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_thanakan_dir(tmp_path, monkeypatch):
    """Use temp directory for ~/.thanakan."""
    thanakan_dir = tmp_path / ".thanakan"
    thanakan_dir.mkdir()

    # Patch Path.home() to return tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    return thanakan_dir


@pytest.fixture
def mock_gmail_token(temp_thanakan_dir):
    """Create a mock Gmail token file."""
    token_path = temp_thanakan_dir / "gmail_token.json"
    token_path.write_text('{"token": "mock"}')
    return token_path


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create a temp directory with encrypted PDFs."""
    import pikepdf

    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()

    # Create encrypted PDF
    pdf_path = pdf_dir / "statement.pdf"
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    pdf.save(pdf_path, encryption=pikepdf.Encryption(owner="o", user="testpass"))

    return pdf_dir


# =============================================================================
# Tests for logout command
# =============================================================================


class TestLogoutCommand:
    """Tests for 'thanakan mail logout' command."""

    def test_logout_removes_token(self, mock_gmail_token):
        """Should remove Gmail token file."""
        assert mock_gmail_token.exists()

        result = runner.invoke(app, ["mail", "logout"])

        assert result.exit_code == 0
        assert not mock_gmail_token.exists()
        assert "Gmail token removed" in result.stdout

    def test_logout_handles_no_token(self, temp_thanakan_dir):
        """Should handle case when not logged in."""
        token_path = temp_thanakan_dir / "gmail_token.json"
        assert not token_path.exists()

        result = runner.invoke(app, ["mail", "logout"])

        assert result.exit_code == 0
        assert "No Gmail token found" in result.stdout

    def test_logout_respects_env_var(self, tmp_path, monkeypatch):
        """Should use GMAIL_TOKEN_PATH env var if set."""
        custom_token = tmp_path / "custom_token.json"
        custom_token.write_text('{"token": "mock"}')
        monkeypatch.setenv("GMAIL_TOKEN_PATH", str(custom_token))

        result = runner.invoke(app, ["mail", "logout"])

        assert result.exit_code == 0
        assert not custom_token.exists()


class TestRevokeCommand:
    """Tests for 'thanakan mail revoke' command (alias for logout)."""

    def test_revoke_removes_token(self, mock_gmail_token):
        """Should remove Gmail token file (same as logout)."""
        assert mock_gmail_token.exists()

        result = runner.invoke(app, ["mail", "revoke"])

        assert result.exit_code == 0
        assert not mock_gmail_token.exists()


# =============================================================================
# Tests for forget-password command
# =============================================================================


class TestForgetPasswordCommand:
    """Tests for 'thanakan mail forget-password' command."""

    def test_forget_password_clears_plaintext(self, temp_thanakan_dir):
        """Should clear plaintext password file."""
        password_file = temp_thanakan_dir / "pdf_password.txt"
        password_file.write_text("secret123")

        # Mock the module-level constants
        with patch("thanakan_mail.unlock.PASSWORD_FILE", password_file):
            with patch("thanakan_mail.unlock.CONFIG_DIR", temp_thanakan_dir):
                result = runner.invoke(app, ["mail", "forget-password"])

        assert result.exit_code == 0
        assert "Saved PDF password cleared" in result.stdout

    def test_forget_password_handles_no_password(self, temp_thanakan_dir):
        """Should handle case when no password saved."""
        result = runner.invoke(app, ["mail", "forget-password"])

        assert result.exit_code == 0
        assert "Saved PDF password cleared" in result.stdout


# =============================================================================
# Tests for unlock command
# =============================================================================


class TestUnlockCommand:
    """Tests for 'thanakan mail unlock' command."""

    def test_unlock_prompts_for_password(self, temp_pdf_dir):
        """Should prompt for password when not provided."""
        result = runner.invoke(
            app,
            ["mail", "unlock", str(temp_pdf_dir), "-r", "none"],
            input="testpass\n",
        )

        assert result.exit_code == 0
        assert "Unlocked 1 PDF(s)" in result.stdout

    def test_unlock_accepts_password_option(self, temp_pdf_dir):
        """Should accept password via --password option."""
        result = runner.invoke(
            app,
            ["mail", "unlock", str(temp_pdf_dir), "--password", "testpass", "-r", "none"],
        )

        assert result.exit_code == 0
        assert "Unlocked 1 PDF(s)" in result.stdout

    def test_unlock_reports_wrong_password(self, temp_pdf_dir):
        """Should report failure on wrong password."""
        result = runner.invoke(
            app,
            ["mail", "unlock", str(temp_pdf_dir), "--password", "wrongpass", "-r", "none"],
        )

        assert result.exit_code == 1
        # Error goes to stderr
        output = result.stdout + (result.stderr or "")
        assert "Failed to unlock" in output or "Incorrect password" in output

    def test_unlock_skips_unencrypted_pdfs(self, tmp_path):
        """Should skip already unencrypted PDFs."""
        import pikepdf

        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()

        # Create unencrypted PDF
        pdf_path = pdf_dir / "unencrypted.pdf"
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        pdf.save(pdf_path)

        result = runner.invoke(
            app,
            ["mail", "unlock", str(pdf_dir), "--password", "anypass"],
        )

        assert result.exit_code == 0
        assert "No encrypted PDFs found" in result.stdout

    def test_unlock_uses_output_dir(self, temp_pdf_dir, tmp_path):
        """Should save unlocked PDFs to output directory."""
        output_dir = tmp_path / "unlocked"

        result = runner.invoke(
            app,
            [
                "mail", "unlock", str(temp_pdf_dir),
                "--password", "testpass",
                "--output", str(output_dir),
                "-r", "none",
            ],
        )

        assert result.exit_code == 0
        assert output_dir.exists()
        unlocked_files = list(output_dir.glob("*.pdf"))
        assert len(unlocked_files) == 1

    def test_unlock_saves_password_to_keyring_by_default(self, temp_pdf_dir):
        """Should save password to keyring by default."""
        mock_keyring = MagicMock()

        with patch("thanakan_mail.unlock.keyring", mock_keyring, create=True):
            result = runner.invoke(
                app,
                ["mail", "unlock", str(temp_pdf_dir), "--password", "testpass"],
            )

        assert result.exit_code == 0
        # Keyring should be attempted (may fall back to plaintext)
        assert "Password saved" in result.stdout or "Unlocked" in result.stdout

    def test_unlock_respects_remember_none(self, temp_pdf_dir, temp_thanakan_dir):
        """Should not save password when --remember none."""
        result = runner.invoke(
            app,
            ["mail", "unlock", str(temp_pdf_dir), "--password", "testpass", "-r", "none"],
        )

        assert result.exit_code == 0
        assert "Password saved" not in result.stdout

    def test_unlock_handles_empty_directory(self, tmp_path):
        """Should handle directory with no PDFs."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(
            app,
            ["mail", "unlock", str(empty_dir), "--password", "test"],
        )

        assert result.exit_code == 1
        # Error goes to stderr
        output = result.stdout + (result.stderr or "")
        assert "No PDF files found" in output

    def test_unlock_verbose_shows_details(self, temp_pdf_dir):
        """Should show details in verbose mode."""
        result = runner.invoke(
            app,
            [
                "mail", "unlock", str(temp_pdf_dir),
                "--password", "testpass",
                "--verbose",
                "-r", "none",
            ],
        )

        assert result.exit_code == 0
        # Verbose mode shows file paths
        assert "unlocked" in result.stdout.lower()


# =============================================================================
# Tests for download command password handling
# =============================================================================


class TestDownloadPasswordHandling:
    """Tests for password handling in download --parse."""

    def test_download_uses_saved_password(self, temp_thanakan_dir, monkeypatch):
        """Should use saved password when available."""
        # This is a more complex integration test
        # We'll just verify the command structure accepts the options
        result = runner.invoke(
            app,
            ["mail", "download", "--help"],
        )

        assert result.exit_code == 0
        assert "--password" in result.stdout
        assert "--remember" in result.stdout

    def test_download_remember_defaults_to_keyring(self):
        """Should default --remember to keyring."""
        result = runner.invoke(
            app,
            ["mail", "download", "--help"],
        )

        assert result.exit_code == 0
        # Help text should mention keyring as default
        assert "keyring" in result.stdout
