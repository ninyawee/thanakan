"""Thanakan CLI - Accounting software export commands"""

import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

accounting_app = typer.Typer(
    name="accounting",
    help="Export bank statements to accounting software formats (Peak, etc.)",
    no_args_is_help=True,
)


class Language(str, Enum):
    """Preferred language for statement selection."""

    en = "en"
    th = "th"


class BankChoice(str, Enum):
    """Supported banks for email download."""

    kbank = "kbank"
    bbl = "bbl"
    scb = "scb"
    all = "all"


@accounting_app.command()
def peak(
    output: Path = typer.Argument(
        ...,
        help="Output Excel file path (.xlsx)",
    ),
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to PDF file or directory (default: download from email)",
        exists=True,
        readable=True,
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
    bank: BankChoice = typer.Option(
        BankChoice.all,
        "--bank",
        "-b",
        help="Bank to download from (when using email)",
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        help="PDF password (default: env PDF_PASS)",
        envvar="PDF_PASS",
    ),
    language: Language = typer.Option(
        Language.en,
        "--language",
        "-l",
        help="Preferred language for overlapping statements",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output",
    ),
):
    """Export bank statements to Peak Import Statement format.

    By default, downloads statements from email (last 30 days) and exports to Peak.
    Optionally, provide a path to use local PDF files instead.

    Duration format for --since/--until:
        Nd = N days   (e.g., 30d = last 30 days)
        Nw = N weeks  (e.g., 2w = last 2 weeks)
        Nm = N months (e.g., 3m = last 3 months)
        Ny = N years  (e.g., 1y = last year)

    Examples:

        # Download from email (last 30 days) and export
        thanakan acc peak output.xlsx

        # Download from email (last 3 months, KBank only)
        thanakan acc peak output.xlsx --since 3m --bank kbank

        # Download emails from 3 months ago to 1 month ago
        thanakan acc peak output.xlsx --since 3m --until 1m

        # Use local PDF files instead of email
        thanakan acc peak output.xlsx ./statements/
    """
    try:
        from thanakan_statement import consolidate_by_account
        import thanakan_accounting  # noqa: F401
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        typer.echo("Install with: uv sync", err=True)
        raise typer.Exit(1)

    pwd = password

    # Determine source: local path or email download
    if path is not None:
        # Use local PDF files
        statements = _parse_local_pdfs(path, pwd, verbose)
    else:
        # Download from email
        statements = _download_and_parse(bank, since, until, pwd, verbose)

    if not statements:
        typer.echo("No statements found", err=True)
        raise typer.Exit(1)

    # Consolidate by account
    accounts = consolidate_by_account(statements, preferred_language=language.value)
    typer.echo(f"Found {len(accounts)} account(s)", err=True)

    if not accounts:
        typer.echo("No accounts to export", err=True)
        raise typer.Exit(1)

    # TUI multi-select for accounts
    selected_accounts = _select_accounts(accounts)

    if not selected_accounts:
        typer.echo("No accounts selected", err=True)
        raise typer.Exit(0)

    # Export each selected account to separate file
    from thanakan_accounting import export_single_to_peak

    typer.echo("\nExported:", err=True)
    for acc in selected_accounts:
        acc_num = acc.account_number.replace("-", "")
        out_file = output.parent / f"{output.stem}_{acc_num}.xlsx"
        try:
            export_single_to_peak(acc, out_file)
            typer.echo(f"  {out_file}", err=True)
        except Exception as e:
            typer.echo(f"  Error exporting {acc.account_number}: {e}", err=True)


def _select_accounts(accounts):
    """Interactive TUI to select accounts for export."""
    import questionary

    # Build choices for TUI
    choices = [
        questionary.Choice(
            title=f"{acc.account_number} ({len(acc.all_transactions)} txns)",
            value=acc,
            checked=True,  # default all selected
        )
        for acc in accounts
    ]

    # Interactive TUI: spacebar to toggle, enter to confirm
    selected = questionary.checkbox(
        "Select accounts to export (spacebar to toggle, enter to confirm):",
        choices=choices,
    ).ask()

    return selected or []


def _parse_local_pdfs(path: Path, password: str, verbose: bool):
    """Parse PDFs from local path."""
    from thanakan_statement import parse_all_pdfs, parse_pdf

    try:
        if path.is_file():
            if verbose:
                typer.echo(f"Parsing: {path}", err=True)
            return [parse_pdf(path, password=password)]
        else:
            if verbose:
                typer.echo(f"Scanning directory: {path}", err=True)
            statements = parse_all_pdfs(path, password=password)
            if verbose:
                typer.echo(f"Parsed {len(statements)} statement(s)", err=True)
            return statements
    except Exception as e:
        typer.echo(f"Error parsing PDFs: {e}", err=True)
        raise typer.Exit(1)


def _download_and_parse(
    bank: BankChoice,
    since: str,
    until: str | None,
    password: str,
    verbose: bool,
):
    """Download statements from email and parse them."""
    try:
        from thanakan_mail import (
            GmailProvider,
            StatementDownloader,
            BANK_CONFIGS,
            unlock_pdf,
            is_pdf_encrypted,
        )
        from thanakan_statement import parse_pdf
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        typer.echo("Install thanakan-mail and thanakan-statement", err=True)
        raise typer.Exit(1)

    # Determine banks to process
    if bank == BankChoice.all:
        banks_to_process = list(BANK_CONFIGS.keys())
    else:
        banks_to_process = [bank.value]

    # Initialize Gmail provider
    try:
        provider = GmailProvider()
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("\nRun 'thanakan mail auth' first to authenticate with Gmail", err=True)
        raise typer.Exit(1)

    if verbose:
        range_desc = f"since {since}"
        if until:
            range_desc += f" until {until}"
        typer.echo(f"Downloading statements ({range_desc})...", err=True)

    # Download to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        all_pdf_paths: list[Path] = []

        for bank_code in banks_to_process:
            if verbose:
                typer.echo(f"  Searching {bank_code.upper()}...", err=True)

            bank_config = BANK_CONFIGS[bank_code]
            downloader = StatementDownloader(provider, bank_config, tmpdir_path)
            results = downloader.download_statements(
                max_emails=100,
                since=since,
                until=until,
                verbose=False,
            )

            # Collect downloaded PDFs
            for r in results:
                for filename in r.downloaded_files:
                    all_pdf_paths.append(tmpdir_path / filename)

            pdfs_count = sum(len(r.downloaded_files) for r in results)
            if verbose:
                typer.echo(f"    Found {pdfs_count} PDF(s)", err=True)

        if not all_pdf_paths:
            typer.echo("No PDFs found in email", err=True)
            return []

        typer.echo(f"Downloaded {len(all_pdf_paths)} PDF(s) from email", err=True)

        # Unlock and parse each PDF
        statements = []
        for pdf_path in all_pdf_paths:
            try:
                # Unlock if encrypted
                if is_pdf_encrypted(pdf_path):
                    unlocked_path = pdf_path.with_suffix(".unlocked.pdf")
                    unlock_pdf(pdf_path, unlocked_path, password)
                    pdf_path = unlocked_path

                stmt = parse_pdf(pdf_path, password=password)
                statements.append(stmt)
                if verbose:
                    typer.echo(f"  Parsed: {stmt.account_number} ({stmt.bank})", err=True)
            except Exception as e:
                if verbose:
                    typer.echo(f"  Failed to parse {pdf_path.name}: {e}", err=True)

        typer.echo(f"Parsed {len(statements)} statement(s)", err=True)
        return statements
