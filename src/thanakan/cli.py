"""Thanakan CLI - Thai bank slip QR parser"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from PIL import Image
from thanakan_qr import SlipQRData, not_bank_slip, expect_single_qrcode

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
):
    """Parse QR code from slip image or raw string."""
    if raw:
        try:
            data = SlipQRData.create_from_code(raw)
            print(data.model_dump_json(indent=2))
        except not_bank_slip as e:
            typer.echo(f"Error: Not a valid bank slip QR - {e}", err=True)
            raise typer.Exit(1)
    elif image:
        try:
            pil_image = Image.open(image)
            data = SlipQRData.create_from_image(pil_image)
            print(data.model_dump_json(indent=2))
        except expect_single_qrcode:
            typer.echo("Error: Expected exactly one QR code in image", err=True)
            raise typer.Exit(1)
        except not_bank_slip as e:
            typer.echo(f"Error: Not a valid bank slip QR - {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo("Error: Provide either an image path or --raw string", err=True)
        raise typer.Exit(1)


@app.command()
def version():
    """Show version."""
    from thanakan import __version__
    typer.echo(f"thanakan {__version__}")


if __name__ == "__main__":
    app()
