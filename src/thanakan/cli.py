"""Thanakan CLI - Thai bank slip QR parser"""

import sys
from io import BytesIO
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="thanakan",
    help="Thai bank slip QR parser",
    no_args_is_help=True,
)


def _is_image_data(data: bytes) -> bool:
    """Detect if data is an image based on magic bytes."""
    if data.startswith(b"\x89PNG"):  # PNG
        return True
    if data.startswith(b"\xff\xd8\xff"):  # JPEG
        return True
    if data.startswith(b"GIF8"):  # GIF
        return True
    if data.startswith(b"RIFF") and len(data) > 12 and data[8:12] == b"WEBP":
        return True
    if data.startswith(b"BM"):  # BMP
        return True
    return False


@app.command()
def qr(
    image: Optional[Path] = typer.Argument(
        None,
        help="Path to slip image file (or pipe image/text via stdin)",
    ),
    raw: Optional[str] = typer.Option(
        None,
        "--raw", "-r",
        help="Raw QR code string to parse",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show verbose output with next steps",
    ),
):
    """Parse QR code from slip image or raw string.

    Supports reading from stdin when piped:

        echo "QR_DATA" | thanakan qr

        cat slip.png | thanakan qr
    """
    try:
        from PIL import Image as PILImage
        from thanakan_qr import SlipQRData, not_bank_slip, expect_single_qrcode
    except ImportError as e:
        if "zbar" in str(e).lower():
            typer.echo("Error: Missing zbar library\n", err=True)
            typer.echo("Install it:", err=True)
            typer.echo("  Ubuntu/Debian: sudo apt-get install libzbar0", err=True)
            typer.echo("  macOS: brew install zbar", err=True)
        else:
            typer.echo(f"Error: Missing dependency - {e}", err=True)
        raise typer.Exit(1)

    # Auto-detect JSON indentation: pretty for terminal, compact for pipes
    indent = 2 if sys.stdout.isatty() else None

    def output_result(data):
        print(data.model_dump_json(indent=indent))
        if verbose:
            _print_next_steps(data)

    # Priority: --raw > image argument > stdin
    if raw:
        try:
            data = SlipQRData.create_from_code(raw)
            output_result(data)
        except not_bank_slip as e:
            typer.echo(f"Error: Not a valid bank slip QR - {e}", err=True)
            if verbose:
                typer.echo("\nPossible causes:", err=True)
                typer.echo("  - QR code is not from a Thai bank slip", err=True)
                typer.echo("  - QR data is corrupted or incomplete", err=True)
                typer.echo("  - CRC checksum mismatch", err=True)
            raise typer.Exit(1)
    elif image:
        try:
            if verbose:
                typer.echo(f"Reading image: {image}", err=True)
            pil_image = PILImage.open(image)
            data = SlipQRData.create_from_image(pil_image)
            output_result(data)
        except expect_single_qrcode:
            typer.echo("Error: Expected exactly one QR code in image", err=True)
            if verbose:
                typer.echo("\nPossible causes:", err=True)
                typer.echo("  - Image contains no QR code", err=True)
                typer.echo("  - Image contains multiple QR codes", err=True)
                typer.echo("  - QR code is too blurry or damaged", err=True)
            raise typer.Exit(1)
        except not_bank_slip as e:
            typer.echo(f"Error: Not a valid bank slip QR - {e}", err=True)
            if verbose:
                typer.echo("\nPossible causes:", err=True)
                typer.echo("  - QR code is not from a Thai bank slip", err=True)
                typer.echo("  - QR data is corrupted or incomplete", err=True)
            raise typer.Exit(1)
    elif not sys.stdin.isatty():
        # Read from stdin - detect if image or text
        try:
            stdin_data = sys.stdin.buffer.read()
            if not stdin_data:
                typer.echo("Error: No data received from stdin", err=True)
                raise typer.Exit(1)

            if _is_image_data(stdin_data):
                if verbose:
                    typer.echo("Reading image from stdin", err=True)
                pil_image = PILImage.open(BytesIO(stdin_data))
                data = SlipQRData.create_from_image(pil_image)
            else:
                if verbose:
                    typer.echo("Reading QR code string from stdin", err=True)
                code = stdin_data.decode("utf-8").strip()
                data = SlipQRData.create_from_code(code)

            output_result(data)
        except expect_single_qrcode:
            typer.echo("Error: Expected exactly one QR code in image", err=True)
            if verbose:
                typer.echo("\nPossible causes:", err=True)
                typer.echo("  - Image contains no QR code", err=True)
                typer.echo("  - Image contains multiple QR codes", err=True)
                typer.echo("  - QR code is too blurry or damaged", err=True)
            raise typer.Exit(1)
        except not_bank_slip as e:
            typer.echo(f"Error: Not a valid bank slip QR - {e}", err=True)
            if verbose:
                typer.echo("\nPossible causes:", err=True)
                typer.echo("  - QR code is not from a Thai bank slip", err=True)
                typer.echo("  - QR data is corrupted or incomplete", err=True)
                typer.echo("  - CRC checksum mismatch", err=True)
            raise typer.Exit(1)
        except UnicodeDecodeError:
            typer.echo("Error: Could not decode stdin as UTF-8 text", err=True)
            raise typer.Exit(1)
        except OSError as e:
            typer.echo(f"Error: Could not read image from stdin - {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo("Error: Provide an image path, --raw string, or pipe data via stdin", err=True)
        raise typer.Exit(1)


def _print_next_steps(data):
    """Print next steps after successful QR parsing."""
    typer.echo("\n--- Next Steps ---", err=True)
    typer.echo("To verify this slip with bank API:", err=True)
    typer.echo(f"  sending_bank_id: {data.payload.sending_bank_id}", err=True)
    typer.echo(f"  transaction_ref: {data.payload.transaction_ref_id}", err=True)
    typer.echo("\nExample (Python):", err=True)
    typer.echo("  from thanakan import KBankAPI  # or SCBAPI", err=True)
    typer.echo("  api = KBankAPI(consumer_id, consumer_secret, cert)", err=True)
    typer.echo(f'  result = await api.verify_slip("{data.payload.sending_bank_id}", "{data.payload.transaction_ref_id}")', err=True)


@app.command()
def version():
    """Show version."""
    from thanakan import __version__
    typer.echo(f"thanakan {__version__}")


# Register subcommand groups (imported at module level for typer registration)
from thanakan.cli_statement import statement_app  # noqa: E402
from thanakan.cli_mail import mail_app  # noqa: E402

app.add_typer(statement_app, name="statement")
app.add_typer(statement_app, name="stm", hidden=True)
app.add_typer(mail_app, name="mail")

try:
    from thanakan.cli_accounting import accounting_app
    app.add_typer(accounting_app, name="accounting")
    app.add_typer(accounting_app, name="acc", hidden=True)
except ImportError:
    pass  # Accounting commands not available if dependencies missing


if __name__ == "__main__":
    app()
