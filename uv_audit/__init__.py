__version__ = "0.1.0"

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from .file_handler import handle_file

app = typer.Typer(
    help="uv-audit: pip-audit like vulnerability scanning but fast",
    no_args_is_help=True,
)


@app.command()
def cmd(
    project: str | None = typer.Argument(
        None, help="optional argument (e.g. directory path)"
    ),
    requirements_files: list[Path] = typer.Option(
        [],
        "-r",
        "--requirement",
        help="requirements file to audit (can be used multiple times: -r requirements.txt -r requirements-dev.txt)",
    ),
    version: Annotated[
        bool,
        typer.Option(
            help="You want to list entitlements in the SANDBOX folder",
            show_default=False,
        ),
    ] = False,
):
    if version:
        rprint(f"[bold]uv-audit {__version__}[/bold]")
        return

    if not requirements_files and not project:
        rprint("[red]Error: No requirements files or project directory provided.[/red]")
        raise typer.Exit(code=1)

    all_vulns = []
    if project:
        vulns = handle_file(project, is_file=False)
        all_vulns.extend(vulns)
    for file_path in requirements_files:
        if not file_path.exists():
            rprint(f"[red]Error: {file_path} does not exist.")
            continue

        if not file_path.is_file():
            rprint(f"[red]Error: {file_path} is not a file.")
            continue
        vulns = handle_file(file_path=file_path, is_file=True)
        all_vulns.extend(vulns)

    if all_vulns:
        sys.exit("Vulnerabilites found")


def main():
    app()
