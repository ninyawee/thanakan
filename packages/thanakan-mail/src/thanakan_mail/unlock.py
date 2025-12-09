"""Unlock password-protected PDF files."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pikepdf

# Config directory for storing password
CONFIG_DIR = Path.home() / ".thanakan"
PASSWORD_FILE = CONFIG_DIR / "pdf_password.txt"
KEYRING_SERVICE = "thanakan-pdf"
KEYRING_USERNAME = "pdf-password"


def get_saved_password() -> str | None:
    """Get saved password from keyring or plaintext file.

    Tries keyring first, then falls back to plaintext file.

    Returns:
        Saved password or None if not found
    """
    # Try keyring first
    try:
        import keyring

        password = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if password:
            return password
    except ImportError:
        pass
    except Exception:
        pass

    # Fall back to plaintext file
    if PASSWORD_FILE.exists():
        return PASSWORD_FILE.read_text().strip()

    return None


def save_password(password: str, use_keyring: bool = True) -> bool:
    """Save password to keyring or plaintext file.

    Args:
        password: Password to save
        use_keyring: If True, try keyring first; if False, use plaintext file

    Returns:
        True if saved successfully
    """
    if use_keyring:
        try:
            import keyring

            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, password)
            return True
        except ImportError:
            pass
        except Exception:
            pass

    # Fall back to plaintext file
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PASSWORD_FILE.write_text(password)
    PASSWORD_FILE.chmod(0o600)  # Read/write only for owner
    return True


def clear_saved_password() -> None:
    """Clear saved password from both keyring and plaintext file."""
    # Clear keyring
    try:
        import keyring

        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except ImportError:
        pass
    except Exception:
        pass

    # Clear plaintext file
    if PASSWORD_FILE.exists():
        PASSWORD_FILE.unlink()


def unlock_pdf(
    input_path: Path | str,
    output_path: Path | str | None = None,
    password: str | None = None,
) -> Path:
    """Unlock a password-protected PDF and save it.

    Args:
        input_path: Path to encrypted PDF
        output_path: Path to save unlocked PDF (default: same as input with _unlocked suffix)
        password: PDF password (required)

    Returns:
        Path to the unlocked PDF file

    Raises:
        pikepdf.PasswordError: If password is incorrect
        FileNotFoundError: If input file doesn't exist
        ValueError: If password is not provided
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"PDF not found: {input_path}")

    if not password:
        raise ValueError("Password is required")

    if output_path is None:
        # Default: input_unlocked.pdf
        output_path = input_path.parent / f"{input_path.stem}_unlocked{input_path.suffix}"
    else:
        output_path = Path(output_path)

    with pikepdf.open(input_path, password=password) as pdf:
        # Save without encryption
        pdf.save(output_path)

    return output_path


def unlock_pdfs(
    pdf_paths: list[Path],
    output_dir: Path | None = None,
    password: str | None = None,
    progress_callback: Callable[[int, int, Path], None] | None = None,
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Unlock multiple PDFs.

    Args:
        pdf_paths: List of PDF file paths
        output_dir: Directory to save unlocked PDFs (default: same directory as input)
        password: PDF password (required)
        progress_callback: Optional callback(current, total, path) for progress updates

    Returns:
        Tuple of (successful paths, failed paths with error messages)

    Raises:
        ValueError: If password is not provided
    """
    if not password:
        raise ValueError("Password is required")

    successful: list[Path] = []
    failed: list[tuple[Path, str]] = []
    total = len(pdf_paths)

    for i, pdf_path in enumerate(pdf_paths):
        if progress_callback:
            progress_callback(i + 1, total, pdf_path)

        try:
            if output_dir:
                output_path = output_dir / f"{pdf_path.stem}_unlocked{pdf_path.suffix}"
            else:
                output_path = None

            unlocked_path = unlock_pdf(pdf_path, output_path, password)
            successful.append(unlocked_path)
        except pikepdf.PasswordError:
            failed.append((pdf_path, "Incorrect password"))
        except Exception as e:
            failed.append((pdf_path, str(e)))

    return successful, failed


def is_pdf_encrypted(pdf_path: Path | str) -> bool:
    """Check if a PDF is password-protected.

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if PDF is encrypted, False otherwise
    """
    try:
        with pikepdf.open(pdf_path) as _:
            return False
    except pikepdf.PasswordError:
        return True
    except Exception:
        return False
