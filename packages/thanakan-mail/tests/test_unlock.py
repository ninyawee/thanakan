"""Tests for PDF unlock functionality."""

from unittest.mock import patch, MagicMock

import pytest
import pikepdf

from thanakan_mail.unlock import (
    get_saved_password,
    save_password,
    clear_saved_password,
    unlock_pdf,
    unlock_pdfs,
    is_pdf_encrypted,
    KEYRING_SERVICE,
    KEYRING_USERNAME,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_password_file(tmp_path, monkeypatch):
    """Use temp directory for password file."""
    test_config_dir = tmp_path / ".thanakan"
    test_password_file = test_config_dir / "pdf_password.txt"
    monkeypatch.setattr("thanakan_mail.unlock.CONFIG_DIR", test_config_dir)
    monkeypatch.setattr("thanakan_mail.unlock.PASSWORD_FILE", test_password_file)
    return test_password_file


@pytest.fixture
def encrypted_pdf(tmp_path):
    """Create a password-protected PDF for testing."""
    pdf_path = tmp_path / "encrypted.pdf"

    # Create a simple PDF and encrypt it
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    pdf.save(
        pdf_path,
        encryption=pikepdf.Encryption(owner="owner123", user="user123"),
    )
    return pdf_path


@pytest.fixture
def unencrypted_pdf(tmp_path):
    """Create an unencrypted PDF for testing."""
    pdf_path = tmp_path / "unencrypted.pdf"

    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    pdf.save(pdf_path)
    return pdf_path


# =============================================================================
# Tests for password storage
# =============================================================================


class TestGetSavedPassword:
    """Tests for get_saved_password function."""

    def test_returns_none_when_no_password_saved(self, temp_password_file):
        """Should return None when no password is saved."""
        with patch.dict("sys.modules", {"keyring": None}):
            result = get_saved_password()
            assert result is None

    def test_returns_password_from_plaintext_file(self, temp_password_file):
        """Should return password from plaintext file."""
        # Setup: create password file
        temp_password_file.parent.mkdir(parents=True, exist_ok=True)
        temp_password_file.write_text("mypassword123")

        with patch.dict("sys.modules", {"keyring": None}):
            result = get_saved_password()
            assert result == "mypassword123"

    def test_strips_whitespace_from_plaintext_password(self, temp_password_file):
        """Should strip whitespace from plaintext password."""
        temp_password_file.parent.mkdir(parents=True, exist_ok=True)
        temp_password_file.write_text("  mypassword123  \n")

        with patch.dict("sys.modules", {"keyring": None}):
            result = get_saved_password()
            assert result == "mypassword123"

    def test_prefers_keyring_over_plaintext(self, temp_password_file):
        """Should prefer keyring password over plaintext file."""
        # Setup plaintext file
        temp_password_file.parent.mkdir(parents=True, exist_ok=True)
        temp_password_file.write_text("plaintext_pass")

        # Mock keyring
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = "keyring_pass"

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            with patch("thanakan_mail.unlock.keyring", mock_keyring, create=True):
                # Need to reimport to get patched version
                from thanakan_mail import unlock
                result = unlock.get_saved_password()
                assert result == "keyring_pass"

    def test_falls_back_to_plaintext_when_keyring_empty(self, temp_password_file):
        """Should fall back to plaintext when keyring returns None."""
        temp_password_file.parent.mkdir(parents=True, exist_ok=True)
        temp_password_file.write_text("plaintext_pass")

        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = None

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            with patch("thanakan_mail.unlock.keyring", mock_keyring, create=True):
                from thanakan_mail import unlock
                result = unlock.get_saved_password()
                assert result == "plaintext_pass"


class TestSavePassword:
    """Tests for save_password function."""

    def test_saves_to_plaintext_when_keyring_false(self, temp_password_file):
        """Should save to plaintext file when use_keyring=False."""
        result = save_password("testpass", use_keyring=False)

        assert result is True
        assert temp_password_file.exists()
        assert temp_password_file.read_text() == "testpass"

    def test_sets_restrictive_permissions_on_plaintext(self, temp_password_file):
        """Should set 600 permissions on plaintext file."""
        save_password("testpass", use_keyring=False)

        # Check file permissions (owner read/write only)
        mode = temp_password_file.stat().st_mode & 0o777
        assert mode == 0o600

    def test_creates_config_directory_if_missing(self, temp_password_file):
        """Should create config directory if it doesn't exist."""
        assert not temp_password_file.parent.exists()

        save_password("testpass", use_keyring=False)

        assert temp_password_file.parent.exists()
        assert temp_password_file.exists()

    def test_falls_back_to_plaintext_when_keyring_unavailable(self, temp_password_file):
        """Should fall back to plaintext when keyring is not available."""
        with patch.dict("sys.modules", {"keyring": None}):
            result = save_password("testpass", use_keyring=True)

            assert result is True
            assert temp_password_file.exists()


class TestClearSavedPassword:
    """Tests for clear_saved_password function."""

    def test_removes_plaintext_file(self, temp_password_file):
        """Should remove plaintext password file."""
        temp_password_file.parent.mkdir(parents=True, exist_ok=True)
        temp_password_file.write_text("testpass")

        clear_saved_password()

        assert not temp_password_file.exists()

    def test_handles_missing_plaintext_file(self, temp_password_file):
        """Should not error when plaintext file doesn't exist."""
        assert not temp_password_file.exists()

        # Should not raise
        clear_saved_password()

    def test_clears_keyring_password(self, temp_password_file):
        """Should attempt to clear keyring password."""
        mock_keyring = MagicMock()

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            # Re-import to pick up the mock
            import importlib
            import thanakan_mail.unlock as unlock_module
            importlib.reload(unlock_module)

            unlock_module.clear_saved_password()

            mock_keyring.delete_password.assert_called_once_with(
                KEYRING_SERVICE, KEYRING_USERNAME
            )


# =============================================================================
# Tests for PDF operations
# =============================================================================


class TestIsEncrypted:
    """Tests for is_pdf_encrypted function."""

    def test_returns_true_for_encrypted_pdf(self, encrypted_pdf):
        """Should return True for encrypted PDF."""
        result = is_pdf_encrypted(encrypted_pdf)
        assert result is True

    def test_returns_false_for_unencrypted_pdf(self, unencrypted_pdf):
        """Should return False for unencrypted PDF."""
        result = is_pdf_encrypted(unencrypted_pdf)
        assert result is False

    def test_returns_false_for_nonexistent_file(self, tmp_path):
        """Should return False for non-existent file."""
        result = is_pdf_encrypted(tmp_path / "nonexistent.pdf")
        assert result is False


class TestUnlockPdf:
    """Tests for unlock_pdf function."""

    def test_unlocks_encrypted_pdf(self, encrypted_pdf, tmp_path):
        """Should unlock encrypted PDF with correct password."""
        output_path = tmp_path / "unlocked.pdf"

        result = unlock_pdf(encrypted_pdf, output_path, password="user123")

        assert result == output_path
        assert output_path.exists()
        assert not is_pdf_encrypted(output_path)

    def test_creates_default_output_path(self, encrypted_pdf):
        """Should create _unlocked suffix when no output specified."""
        result = unlock_pdf(encrypted_pdf, password="user123")

        expected = encrypted_pdf.parent / "encrypted_unlocked.pdf"
        assert result == expected
        assert expected.exists()

    def test_raises_on_wrong_password(self, encrypted_pdf, tmp_path):
        """Should raise PasswordError on wrong password."""
        output_path = tmp_path / "unlocked.pdf"

        with pytest.raises(pikepdf.PasswordError):
            unlock_pdf(encrypted_pdf, output_path, password="wrongpass")

    def test_raises_on_missing_password(self, encrypted_pdf):
        """Should raise ValueError when password not provided."""
        with pytest.raises(ValueError, match="Password is required"):
            unlock_pdf(encrypted_pdf, password=None)

    def test_raises_on_missing_file(self, tmp_path):
        """Should raise FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            unlock_pdf(tmp_path / "missing.pdf", password="test")


class TestUnlockPdfs:
    """Tests for unlock_pdfs function."""

    def test_unlocks_multiple_pdfs(self, tmp_path):
        """Should unlock multiple PDFs."""
        # Create multiple encrypted PDFs
        pdf_paths = []
        for i in range(3):
            pdf_path = tmp_path / f"encrypted_{i}.pdf"
            pdf = pikepdf.Pdf.new()
            pdf.add_blank_page(page_size=(612, 792))
            pdf.save(pdf_path, encryption=pikepdf.Encryption(owner="o", user="pass"))
            pdf_paths.append(pdf_path)

        successful, failed = unlock_pdfs(pdf_paths, password="pass")

        assert len(successful) == 3
        assert len(failed) == 0

    def test_reports_failures(self, tmp_path):
        """Should report failed unlocks."""
        # Create one encrypted PDF with known password
        pdf_path = tmp_path / "encrypted.pdf"
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        pdf.save(pdf_path, encryption=pikepdf.Encryption(owner="o", user="realpass"))

        successful, failed = unlock_pdfs([pdf_path], password="wrongpass")

        assert len(successful) == 0
        assert len(failed) == 1
        assert failed[0][0] == pdf_path
        assert "password" in failed[0][1].lower()

    def test_calls_progress_callback(self, encrypted_pdf):
        """Should call progress callback for each PDF."""
        callback = MagicMock()

        unlock_pdfs([encrypted_pdf], password="user123", progress_callback=callback)

        callback.assert_called_once_with(1, 1, encrypted_pdf)

    def test_raises_on_missing_password(self, encrypted_pdf):
        """Should raise ValueError when password not provided."""
        with pytest.raises(ValueError, match="Password is required"):
            unlock_pdfs([encrypted_pdf], password=None)

    def test_uses_output_dir(self, encrypted_pdf, tmp_path):
        """Should save unlocked PDFs to specified output directory."""
        output_dir = tmp_path / "unlocked"
        output_dir.mkdir()

        successful, _ = unlock_pdfs([encrypted_pdf], output_dir, password="user123")

        assert len(successful) == 1
        assert successful[0].parent == output_dir
        assert "unlocked" in successful[0].name
