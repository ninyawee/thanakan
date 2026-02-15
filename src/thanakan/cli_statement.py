"""Thanakan CLI - Thai bank PDF statement parser commands"""

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

statement_app = typer.Typer(
    name="statement",
    help="Parse Thai bank PDF statements (KBank, BBL)",
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Output format for export command."""

    json = "json"
    csv = "csv"
    excel = "excel"


class Language(str, Enum):
    """Preferred language for statement selection."""

    en = "en"
    th = "th"


@statement_app.command()
def parse(
    path: Path = typer.Argument(
        ...,
        help="Path to PDF file or directory containing PDFs",
        exists=True,
        readable=True,
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        help="PDF password (default: env PDF_PASS)",
        envvar="PDF_PASS",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output with parsing details",
    ),
):
    """Parse PDF statement(s) and output JSON to stdout.

    Accepts a single PDF file or a directory of PDFs.
    Auto-detects bank type (KBank, BBL) and language (Thai/English).
    """
    try:
        from thanakan_statement import parse_all_pdfs, parse_pdf
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        typer.echo("Install with: uv sync", err=True)
        raise typer.Exit(1)

    pwd = password

    try:
        if path.is_file():
            if verbose:
                typer.echo(f"Parsing: {path}", err=True)
            statement = parse_pdf(path, password=pwd)
            print(statement.model_dump_json(indent=2))
            if verbose:
                _print_parse_summary([statement])
        elif path.is_dir():
            if verbose:
                typer.echo(f"Scanning directory: {path}", err=True)
            statements = parse_all_pdfs(path, password=pwd)
            if not statements:
                typer.echo("No PDFs found or parsed", err=True)
                raise typer.Exit(1)
            output = [s.model_dump(mode="json") for s in statements]
            print(json.dumps(output, indent=2, default=str))
            if verbose:
                _print_parse_summary(statements)
        else:
            typer.echo(f"Error: {path} is not a file or directory", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error parsing PDF: {e}", err=True)
        raise typer.Exit(1)


@statement_app.command("export")
def export_cmd(
    path: Path = typer.Argument(
        ...,
        help="Path to PDF file or directory containing PDFs",
        exists=True,
        readable=True,
    ),
    output: Path = typer.Argument(
        ...,
        help="Output path (file for JSON/Excel, directory for CSV)",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.json,
        "--format",
        "-f",
        help="Output format",
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
    """Parse PDFs, consolidate by account, and export to file.

    Full pipeline: parse -> consolidate -> deduplicate -> export.
    For CSV format, output path should be a directory (one file per account).
    """
    try:
        from thanakan_statement import (
            consolidate_by_account,
            export_to_csv,
            export_to_excel,
            export_to_json,
            parse_all_pdfs,
            parse_pdf,
        )
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        raise typer.Exit(1)

    pwd = password

    # Parse PDFs
    try:
        if path.is_file():
            statements = [parse_pdf(path, password=pwd)]
        else:
            statements = parse_all_pdfs(path, password=pwd)

        if not statements:
            typer.echo("No PDFs found or parsed", err=True)
            raise typer.Exit(1)

        if verbose:
            typer.echo(f"Parsed {len(statements)} statement(s)", err=True)
    except Exception as e:
        typer.echo(f"Error parsing PDFs: {e}", err=True)
        raise typer.Exit(1)

    # Consolidate
    accounts = consolidate_by_account(statements, preferred_language=language.value)
    if verbose:
        typer.echo(f"Consolidated into {len(accounts)} account(s)", err=True)
        for acc in accounts:
            typer.echo(
                f"  {acc.account_number}: {len(acc.all_transactions)} transactions",
                err=True,
            )

    # Export
    try:
        if format == OutputFormat.json:
            export_to_json(accounts, output)
            typer.echo(f"Exported to {output}", err=True)
        elif format == OutputFormat.csv:
            export_to_csv(accounts, output)
            typer.echo(f"Exported CSVs to {output}/", err=True)
        elif format == OutputFormat.excel:
            export_to_excel(accounts, output)
            typer.echo(f"Exported to {output}", err=True)
    except Exception as e:
        typer.echo(f"Error exporting: {e}", err=True)
        raise typer.Exit(1)


@statement_app.command()
def validate(
    path: Path = typer.Argument(
        ...,
        help="Path to PDF file or directory containing PDFs",
        exists=True,
        readable=True,
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        help="PDF password (default: env PDF_PASS)",
        envvar="PDF_PASS",
    ),
):
    """Validate balance continuity across statements.

    Checks that closing balance of each statement matches
    opening balance of the next consecutive statement.
    """
    try:
        from thanakan_statement import parse_all_pdfs, parse_pdf, validate_balance_continuity
        from thanakan_statement.consolidate import group_statements_by_account
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        raise typer.Exit(1)

    pwd = password

    # Parse PDFs
    try:
        if path.is_file():
            statements = [parse_pdf(path, password=pwd)]
        else:
            statements = parse_all_pdfs(path, password=pwd)

        if not statements:
            typer.echo("No PDFs found or parsed", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error parsing PDFs: {e}", err=True)
        raise typer.Exit(1)

    # Group by account and validate each
    groups = group_statements_by_account(statements)
    all_valid = True

    for account_number, account_statements in sorted(groups.items()):
        # Sort by period start
        account_statements.sort(key=lambda s: s.statement_period_start)

        is_valid, issues = validate_balance_continuity(account_statements)

        if is_valid:
            typer.echo(
                f"[OK] {account_number}: {len(account_statements)} statements validated"
            )
        else:
            all_valid = False
            typer.echo(
                f"[FAIL] {account_number}: {len(issues)} issue(s) found", err=True
            )
            for issue in issues:
                typer.echo(
                    f"  - {issue.statement.source_pdf}: "
                    f"expected opening {issue.expected_opening}, "
                    f"got {issue.actual_opening}",
                    err=True,
                )

    if not all_valid:
        raise typer.Exit(1)


@statement_app.command()
def kshop(
    since: str = typer.Option(
        "30d",
        "--since",
        "-s",
        help="Fetch emails from this duration ago (e.g., 30d, 2w, 3m, 1y)",
    ),
    until: Optional[str] = typer.Option(
        None,
        "--until",
        "-u",
        help="Fetch emails until this duration ago (e.g., 7d, 1w)",
    ),
    max_emails: int = typer.Option(
        100,
        "--max",
        "-m",
        help="Maximum emails to process",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output JSON file (default: stdout)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output",
    ),
):
    """Fetch and parse KShop (K PLUS SHOP) daily summary emails from Gmail.

    Reads KShop daily sales summary emails and extracts store name,
    store ID, daily amount, and bank account number.

    Requires Gmail authentication (run 'thanakan mail auth' first).

    Examples:

        thanakan stm kshop

        thanakan stm kshop --since 60d --output kshop.json

        thanakan stm kshop --since 3m -v
    """
    try:
        from thanakan_mail import fetch_kshop_summaries, save_kshop_json
    except ImportError as e:
        typer.echo(f"Error: Missing dependency - {e}", err=True)
        typer.echo("Install with: uv sync", err=True)
        raise typer.Exit(1)

    try:
        summaries = fetch_kshop_summaries(
            max_emails=max_emails,
            since=since,
            until=until,
            verbose=verbose,
        )
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("\nRun 'thanakan mail auth' first", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if not summaries:
        typer.echo("No KShop emails found", err=True)
        raise typer.Exit(1)

    if output:
        save_kshop_json(summaries, output)
        typer.echo(f"Exported {len(summaries)} summaries to {output}", err=True)

    # When piped, output JSON for machine consumption
    if not sys.stdout.isatty():
        data = [s.model_dump(mode="json") for s in summaries]
        print(json.dumps(data, default=str, ensure_ascii=False))
        return

    # Display tables grouped by store
    from collections import defaultdict
    from decimal import Decimal
    from email.utils import parsedate_to_datetime

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    # Group by store_id
    by_store: dict[str, list] = defaultdict(list)
    for s in summaries:
        by_store[s.store_id].append(s)

    def _parse_date(email_date: str) -> str:
        try:
            return parsedate_to_datetime(email_date).strftime("%Y-%m-%d")
        except Exception:
            return email_date

    grand_total = Decimal(0)
    grand_days = 0

    for store_id, store_summaries in sorted(by_store.items()):
        store_name = store_summaries[0].store_name
        account = store_summaries[0].account_number
        account_name = store_summaries[0].account_name

        # Sort by date descending (newest first)
        store_summaries.sort(
            key=lambda s: _parse_date(s.email_date), reverse=True
        )

        store_total = sum(s.daily_amount for s in store_summaries)
        grand_total += store_total
        grand_days += len(store_summaries)

        # Store header
        header = f"{store_name}  [dim]{store_id}[/dim]"
        if account_name:
            header += f"\n{account}  {account_name}"
        else:
            header += f"\n{account}"

        # Date-Amount table
        table = Table(
            show_header=True,
            title=header,
            title_style="bold green",
            title_justify="left",
        )
        table.add_column("Date", style="cyan")
        table.add_column("Amount (THB)", justify="right", style="bold")

        for s in store_summaries:
            table.add_row(_parse_date(s.email_date), f"{s.daily_amount:,.2f}")

        table.add_section()
        table.add_row(f"{len(store_summaries)} days", f"{store_total:,.2f}")

        console.print(table)
        console.print()

    # Grand total across all stores
    if len(by_store) > 1:
        console.print(
            f"[bold]Total: {grand_days} days, {grand_total:,.2f} THB[/bold]"
        )


def _print_parse_summary(statements):
    """Print parsing summary to stderr."""
    typer.echo("\n--- Summary ---", err=True)
    for stmt in statements:
        typer.echo(
            f"  {stmt.account_number} ({stmt.bank}/{stmt.language}): "
            f"{len(stmt.transactions)} transactions, "
            f"{stmt.statement_period_start} to {stmt.statement_period_end}",
            err=True,
        )
