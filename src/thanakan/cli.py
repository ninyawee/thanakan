"""Thanakan CLI - Thai bank slip QR parser"""

import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="thanakan",
    help="Thai bank slip QR parser",
    no_args_is_help=True,
)


@app.command()
def qr(
    image: Optional[Path] = typer.Argument(
        None,
        help="Path to slip image file",
        exists=True,
        readable=True,
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
    """Parse QR code from slip image or raw string."""
    try:
        from PIL import Image
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

    if raw:
        try:
            data = SlipQRData.create_from_code(raw)
            print(data.model_dump_json(indent=2))
            if verbose:
                _print_next_steps(data)
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
            pil_image = Image.open(image)
            data = SlipQRData.create_from_image(pil_image)
            print(data.model_dump_json(indent=2))
            if verbose:
                _print_next_steps(data)
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
    else:
        typer.echo("Error: Provide either an image path or --raw string", err=True)
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


if __name__ == "__main__":
    app()
