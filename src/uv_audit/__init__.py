__version__ = "0.1.0"

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from .file_handler import handle_file, handle_pyproject
from .pyproject_handler import (
    PyProjectSelection,
    UnknownExtraError,
    UnknownGroupError,
    resolve_selection,
)

app = typer.Typer(
    help="uv-audit: pip-audit like vulnerability scanning but fast",
    no_args_is_help=True,
)


def _is_pyproject(path: Path) -> bool:
    return path.name == "pyproject.toml"


def _warn_selection_flags(
    selection_flags_set: bool, has_requirements: bool, has_pyproject: bool
) -> None:
    if not selection_flags_set or not has_requirements:
        return
    if not has_pyproject:
        rprint(
            "[yellow]Warning: --group/--extra/--all-* flags are ignored for "
            "requirements.txt files.[/yellow]"
        )
    else:
        rprint(
            "[yellow]Warning: --group/--extra/--all-* flags apply only to "
            "pyproject.toml inputs.[/yellow]"
        )


def _process_pyproject(
    path: Path,
    extras: list[str],
    groups: list[str],
    all_extras: bool,
    all_groups: bool,
) -> list[dict]:
    try:
        selection: PyProjectSelection = resolve_selection(
            path=path,
            extras=extras,
            groups=groups,
            all_extras=all_extras,
            all_groups=all_groups,
        )
    except (UnknownExtraError, UnknownGroupError) as exc:
        rprint(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc
    no_deps = (
        not selection.has_main_deps and not selection.extras and not selection.groups
    )
    if no_deps:
        rprint(
            f"[yellow]Warning: {path} has no [project.dependencies] and "
            f"no extras/groups selected.[/yellow]"
        )
    return handle_pyproject(selection)


@app.command()
def cmd(
    project: Annotated[
        str | None,
        typer.Argument(help="Directory containing a pyproject.toml (shortcut)"),
    ] = None,
    requirements_files: Annotated[
        list[Path] | None,
        typer.Option(
            "-r",
            "--requirement",
            help="requirements.txt or pyproject.toml to audit (repeatable)",
        ),
    ] = None,
    groups: Annotated[
        list[str] | None,
        typer.Option("--group", help="Dependency group to include (repeatable)"),
    ] = None,
    extras: Annotated[
        list[str] | None,
        typer.Option("--extra", help="Optional-dependency extra (repeatable)"),
    ] = None,
    all_groups: Annotated[
        bool, typer.Option("--all-groups", help="Include all dependency-groups")
    ] = False,
    all_extras: Annotated[
        bool, typer.Option("--all-extras", help="Include all optional-dependencies")
    ] = False,
    all_: Annotated[
        bool,
        typer.Option("--all", help="Shortcut for --all-groups --all-extras"),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(help="Print version", show_default=False),
    ] = False,
):
    if version:
        rprint(f"[bold]uv-audit {__version__}[/bold]")
        return

    requirements_files = requirements_files or []
    groups = groups or []
    extras = extras or []
    if all_:
        all_groups = True
        all_extras = True

    if not requirements_files and not project:
        rprint("[red]Error: No requirements files or project directory provided.[/red]")
        raise typer.Exit(code=1)

    inputs: list[tuple[Path, str]] = []
    if project:
        inputs.append((Path(project) / "pyproject.toml", "pyproject"))
    for file_path in requirements_files:
        kind = "pyproject" if _is_pyproject(file_path) else "requirements"
        inputs.append((file_path, kind))

    has_pyproject = any(kind == "pyproject" for _, kind in inputs)
    has_requirements = any(kind == "requirements" for _, kind in inputs)
    selection_flags_set = bool(groups or extras or all_groups or all_extras)
    _warn_selection_flags(selection_flags_set, has_requirements, has_pyproject)

    all_vulns: list[dict] = []
    for path, kind in inputs:
        if not path.exists():
            rprint(f"[red]Error: {path} does not exist.[/red]")
            continue
        if not path.is_file():
            rprint(f"[red]Error: {path} is not a file.[/red]")
            continue

        if kind == "pyproject":
            vulns = _process_pyproject(path, extras, groups, all_extras, all_groups)
        else:
            vulns = handle_file(file_path=path, is_file=True)
        all_vulns.extend(vulns)

    if all_vulns:
        sys.exit("Vulnerabilites found")


def main():
    app()
