"""Thanakan CLI - Email download commands"""

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

mail_app = typer.Typer(
    name="mail",
    help="Download bank statement PDFs from email (Gmail)",
    no_args_is_help=True,
)


class BankChoice(str, Enum):
    """Supported banks."""

    kbank = "kbank"
    bbl = "bbl"
    scb = "scb"
    all = "all"


class RememberChoice(str, Enum):
    """Password storage options."""

    none = "none"
    keyring = "keyring"
    plaintext = "plaintext"


@mail_app.command()
def auth(
    client_secret: Optional[Path] = typer.Option(
        None,
        "--client-secret",
        "-c",
        help="Path to Google OAuth client_secret.json (or env: GMAIL_CLIENT_SECRET)",
        envvar="GMAIL_CLIENT_SECRET",
    ),
):
    """Authenticate with Gmail (opens browser for OAuth flow).

    After authentication, token is saved to ~/.thanakan/gmail_token.json
    (or path specified by GMAIL_TOKEN_PATH env var).

    Get client_secret.json from Google Cloud Console:
    https://console.cloud.google.com/apis/credentials
    """
    try:
        from thanakan_mail import GmailProvider
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        typer.echo("Install with: uv sync", err=True)
        raise typer.Exit(1)

    try:
        typer.echo("Starting Gmail OAuth authentication...")
        provider = GmailProvider(client_secret_path=client_secret)
        provider.authenticate()

        profile = provider.get_profile()
        typer.echo(f"Authenticated as: {profile['emailAddress']}")
        typer.echo(f"Total messages: {profile['messagesTotal']}")
        typer.echo(f"Token saved to: {provider.token_path}")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("\nGet client_secret.json from:", err=True)
        typer.echo("  https://console.cloud.google.com/apis/credentials", err=True)
        raise typer.Exit(1)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Authentication failed: {e}", err=True)
        raise typer.Exit(1)


@mail_app.command()
def download(
    bank: BankChoice = typer.Argument(
        ...,
        help="Bank to download from (kbank, bbl, scb, or all)",
    ),
    output: Path = typer.Option(
        Path.cwd() / "downloads",
        "--output",
        "-o",
        help="Directory to save PDFs",
    ),
    since: str = typer.Option(
        "30d",
        "--since",
        "-s",
        help="Download emails from this duration ago (e.g., 30d, 2w, 3m, 1y)",
    ),
    until: Optional[str] = typer.Option(
        None,
        "--until",
        "-u",
        help="Download emails until this duration ago (e.g., 7d, 1w)",
    ),
    max_emails: int = typer.Option(
        100,
        "--max",
        "-m",
        help="Maximum emails to process per bank",
    ),
    parse: bool = typer.Option(
        False,
        "--parse",
        "-p",
        help="Parse PDFs inline using thanakan-statement",
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        help="PDF password for parsing (will prompt if not provided)",
    ),
    remember: RememberChoice = typer.Option(
        RememberChoice.keyring,
        "--remember",
        "-r",
        help="Remember password: 'keyring' (OS secure storage, default), 'plaintext' (~/.thanakan/), or 'none'",
    ),
    save_meta: bool = typer.Option(
        True,
        "--metadata/--no-metadata",
        help="Save email metadata to JSON",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output",
    ),
):
    """Download bank statement PDFs from Gmail.

    Searches for emails from known bank senders with PDF attachments,
    then downloads only statement PDFs (filters out non-statement files).

    Duration format for --since/--until:
        Nd = N days   (e.g., 30d = last 30 days)
        Nw = N weeks  (e.g., 2w = last 2 weeks)
        Nm = N months (e.g., 3m = last 3 months)
        Ny = N years  (e.g., 1y = last year)

    Examples:

        thanakan mail download kbank

        thanakan mail download bbl --since 60d --output ./statements

        thanakan mail download all --since 3m --until 1m
    """
    try:
        from thanakan_mail import (
            GmailProvider,
            StatementDownloader,
            BANK_CONFIGS,
            save_metadata,
        )
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        typer.echo("Install with: uv sync", err=True)
        raise typer.Exit(1)

    # Determine banks to process
    if bank == BankChoice.all:
        banks_to_process = list(BANK_CONFIGS.keys())
    else:
        banks_to_process = [bank.value]

    # Initialize provider
    try:
        provider = GmailProvider()
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("\nRun 'thanakan mail auth' first", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error initializing Gmail: {e}", err=True)
        raise typer.Exit(1)

    # Download from each bank
    total_emails = 0
    total_pdfs = 0
    all_pdf_paths: list[str] = []

    for bank_code in banks_to_process:
        if len(banks_to_process) > 1 or verbose:
            typer.echo(f"\n{'='*50}")
            typer.echo(f"Downloading from {bank_code.upper()}")
            typer.echo("=" * 50)

        try:
            bank_config = BANK_CONFIGS[bank_code]
            downloader = StatementDownloader(provider, bank_config, output)
            results = downloader.download_statements(
                max_emails=max_emails,
                since=since,
                until=until,
                verbose=verbose,
            )

            emails_count = len(results)
            pdfs_count = sum(len(r.downloaded_files) for r in results)
            total_emails += emails_count
            total_pdfs += pdfs_count

            # Collect PDF paths for parsing
            for r in results:
                all_pdf_paths.extend(r.downloaded_files)

            typer.echo(f"{bank_code.upper()}: {pdfs_count} PDFs from {emails_count} emails")

            # Save metadata
            if save_meta and results:
                metadata_path = output / f"metadata_{bank_code}.json"
                save_metadata(results, metadata_path)
                if verbose:
                    typer.echo(f"  Metadata: {metadata_path}")

        except Exception as e:
            typer.echo(f"Error downloading from {bank_code}: {e}", err=True)
            if verbose:
                import traceback

                typer.echo(traceback.format_exc(), err=True)

    # Summary
    typer.echo(f"\n{'='*50}")
    typer.echo(f"TOTAL: {total_pdfs} PDFs from {total_emails} emails")
    typer.echo(f"Saved to: {output}")
    typer.echo("=" * 50)

    # Optional: Parse PDFs inline
    if parse and all_pdf_paths:
        typer.echo("\nParsing downloaded PDFs...")

        # Get password for parsing
        pwd = password

        # Try saved password
        if pwd is None:
            try:
                from thanakan_mail import get_saved_password
                pwd = get_saved_password()
                if pwd and verbose:
                    typer.echo("Using saved password")
            except ImportError:
                pass

        # Prompt for password if not provided
        if pwd is None:
            pwd = typer.prompt("Enter PDF password", hide_input=True)

        if pwd:
            _parse_pdfs(output, pwd, verbose)

            # Save password if requested
            if remember != RememberChoice.none:
                try:
                    from thanakan_mail import save_password
                    use_keyring = remember == RememberChoice.keyring
                    if save_password(pwd, use_keyring=use_keyring):
                        storage = "keyring" if use_keyring else "~/.thanakan/pdf_password.txt"
                        typer.echo(f"Password saved to {storage}")
                except ImportError:
                    pass
        else:
            typer.echo("Error: PDF password required for parsing", err=True)


def _parse_pdfs(directory: Path, password: Optional[str], verbose: bool) -> None:
    """Parse PDFs in directory using thanakan-statement."""
    try:
        from thanakan_statement import parse_all_pdfs
    except ImportError:
        typer.echo("Error: thanakan-statement required for parsing", err=True)
        typer.echo("Install with: uv sync", err=True)
        return

    if not password:
        typer.echo("Error: PDF password required for parsing", err=True)
        return

    try:
        statements = parse_all_pdfs(directory, password=password)
        typer.echo(f"Parsed {len(statements)} statements")

        if verbose:
            for stmt in statements:
                typer.echo(
                    f"  {stmt.account_number} ({stmt.bank}/{stmt.language}): "
                    f"{len(stmt.transactions)} transactions, "
                    f"{stmt.statement_period_start} to {stmt.statement_period_end}",
                    err=True,
                )
    except Exception as e:
        typer.echo(f"Error parsing PDFs: {e}", err=True)


@mail_app.command()
def unlock(
    directory: Path = typer.Argument(
        ...,
        help="Directory containing PDFs to unlock",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        help="PDF password (will prompt if not provided)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for unlocked PDFs (default: same as input)",
    ),
    remember: RememberChoice = typer.Option(
        RememberChoice.keyring,
        "--remember",
        "-r",
        help="Remember password: 'keyring' (OS secure storage, default), 'plaintext' (~/.thanakan/), or 'none'",
    ),
    use_saved: bool = typer.Option(
        True,
        "--use-saved/--no-saved",
        help="Use previously saved password if available",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output",
    ),
):
    """Unlock password-protected PDF files.

    Removes password protection from bank statement PDFs so they can be
    read without entering a password each time.

    Examples:

        thanakan mail unlock ./downloads

        thanakan mail unlock ./downloads --password mypass --remember keyring

        thanakan mail unlock ./downloads -o ./unlocked -r plaintext
    """
    try:
        from thanakan_mail import (
            unlock_pdfs,
            get_saved_password,
            save_password,
            is_pdf_encrypted,
        )
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        typer.echo("Install with: uv sync", err=True)
        raise typer.Exit(1)

    # Find all PDFs
    pdf_files = list(directory.glob("*.pdf")) + list(directory.glob("*.PDF"))
    if not pdf_files:
        typer.echo(f"No PDF files found in {directory}", err=True)
        raise typer.Exit(1)

    # Filter to only encrypted PDFs
    encrypted_pdfs = [p for p in pdf_files if is_pdf_encrypted(p)]
    if not encrypted_pdfs:
        typer.echo("No encrypted PDFs found - all files are already unlocked")
        raise typer.Exit(0)

    typer.echo(f"Found {len(encrypted_pdfs)} encrypted PDF(s)")

    # Get password
    pwd = password

    # Try saved password if enabled
    if pwd is None and use_saved:
        pwd = get_saved_password()
        if pwd and verbose:
            typer.echo("Using saved password")

    # Prompt for password if not provided
    if pwd is None:
        pwd = typer.prompt("Enter PDF password", hide_input=True)

    if not pwd:
        typer.echo("Error: Password is required", err=True)
        raise typer.Exit(1)

    # Create output directory if specified
    if output:
        output.mkdir(parents=True, exist_ok=True)

    # Unlock with progress bar
    try:
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    except ImportError:
        # Fallback without rich progress
        typer.echo("Unlocking PDFs...")
        successful, failed = unlock_pdfs(encrypted_pdfs, output, pwd)
    else:
        successful: list[Path] = []
        failed: list[tuple[Path, str]] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Unlocking PDFs...", total=len(encrypted_pdfs))

            for pdf_path in encrypted_pdfs:
                progress.update(task, description=f"Unlocking {pdf_path.name}")
                try:
                    from thanakan_mail import unlock_pdf

                    if output:
                        out_path = output / f"{pdf_path.stem}_unlocked{pdf_path.suffix}"
                    else:
                        out_path = None

                    unlocked = unlock_pdf(pdf_path, out_path, pwd)
                    successful.append(unlocked)
                except Exception as e:
                    error_msg = "Incorrect password" if "password" in str(e).lower() else str(e)
                    failed.append((pdf_path, error_msg))

                progress.advance(task)

    # Report results
    if successful:
        typer.echo(f"Unlocked {len(successful)} PDF(s)")
        if verbose:
            for path in successful:
                typer.echo(f"  {path}")

    if failed:
        typer.echo(f"Failed to unlock {len(failed)} PDF(s):", err=True)
        for path, error in failed:
            typer.echo(f"  {path.name}: {error}", err=True)

    # Save password if requested and at least one succeeded
    if successful and remember != RememberChoice.none:
        use_keyring = remember == RememberChoice.keyring
        if save_password(pwd, use_keyring=use_keyring):
            storage = "keyring" if use_keyring else "~/.thanakan/pdf_password.txt"
            typer.echo(f"Password saved to {storage}")
        else:
            typer.echo("Warning: Failed to save password", err=True)

    if failed:
        raise typer.Exit(1)


@mail_app.command("forget-password")
def forget_password():
    """Clear saved PDF password from keyring and plaintext storage."""
    try:
        from thanakan_mail import clear_saved_password
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        raise typer.Exit(1)

    clear_saved_password()
    typer.echo("Saved PDF password cleared")


def _logout_gmail() -> None:
    """Internal function to remove Gmail OAuth token."""
    token_path = Path.home() / ".thanakan" / "gmail_token.json"

    # Also check env var
    import os
    token_path_env = os.getenv("GMAIL_TOKEN_PATH")
    if token_path_env:
        token_path = Path(token_path_env)

    if token_path.exists():
        token_path.unlink()
        typer.echo(f"Gmail token removed: {token_path}")
    else:
        typer.echo("No Gmail token found (not logged in)")


@mail_app.command("logout")
def logout():
    """Remove Gmail OAuth token (logout from Gmail).

    After logout, run 'thanakan mail auth' to re-authenticate.
    """
    _logout_gmail()


@mail_app.command("revoke")
def revoke():
    """Alias for 'logout' - remove Gmail OAuth token."""
    _logout_gmail()
