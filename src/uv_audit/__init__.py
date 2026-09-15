"""Entry point for the uv-audit CLI application.

This module wires together the Typer CLI, file/pyproject handling, and
vulnerability reporting. It defines the top-level ``cmd`` command that users
invoke as ``uv-audit``, plus small private helpers used exclusively by that
command.
"""

__version__ = "0.3.3"

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from .discover import (
    DEFAULT_EXCLUDES,
    DEFAULT_INCLUDES,
    discover_files,
    kind_for_path,
)
from .environment_handler import LockAuditError
from .file_handler import handle_file, handle_lock, handle_pyproject
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


def _warn_selection_flags(
    selection_flags_set: bool,
    has_flagless_inputs: bool,
    has_pyproject: bool,
    quiet: bool = False,
) -> None:
    """Emit a warning when group/extra flags are used with incompatible inputs.

    Prints a yellow Rich-formatted warning when the caller supplied
    ``--group``, ``--extra``, ``--all-groups``, or ``--all-extras`` flags
    alongside requirement files for which those flags have no effect.

    Parameters
    ----------
    selection_flags_set : bool
        Whether any of the selection flags (``--group``, ``--extra``,
        ``--all-groups``, ``--all-extras``) were provided by the user.
    has_flagless_inputs : bool
        Whether at least one input the flags do not apply to is present —
        a plain ``requirements.txt`` or a ``uv.lock``.
    has_pyproject : bool
        Whether at least one ``pyproject.toml`` input is present.
    quiet : bool, optional
        When ``True``, suppress all output.  Default is ``False``.
    """
    if not selection_flags_set or not has_flagless_inputs or quiet:
        return
    if not has_pyproject:
        rprint(
            "[yellow]Warning: --group/--extra/--all-* flags are ignored for "
            "requirements.txt and uv.lock files.[/yellow]"
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
    quiet: bool = False,
) -> tuple[list[dict], PyProjectSelection | None]:
    """Resolve a ``pyproject.toml`` selection and run a vulnerability scan.

    Calls :func:`~uv_audit.pyproject_handler.resolve_selection` to determine
    which extras and dependency-groups to install, then delegates to
    :func:`~uv_audit.file_handler.handle_pyproject` for the actual install and
    scan. Exits with code 1 on unknown extras or groups.

    Parameters
    ----------
    path : Path
        Absolute or relative path to the ``pyproject.toml`` file.
    extras : list[str]
        Explicit optional-dependency extras to include.
    groups : list[str]
        Explicit dependency groups to include.
    all_extras : bool
        When ``True``, include every declared optional-dependency extra.
    all_groups : bool
        When ``True``, include every declared dependency group.
    quiet : bool, optional
        When ``True``, suppress all output.  Default is ``False``.

    Returns
    -------
    tuple[list[dict], PyProjectSelection | None]
        A pair of the vulnerability records and the resolved selection.
        On unknown-extra/group errors, exits with code 1 instead of returning.

    Raises
    ------
    typer.Exit
        Raised with exit code 1 when an unknown extra or group is specified.
    """
    try:
        selection: PyProjectSelection = resolve_selection(
            path=path,
            extras=extras,
            groups=groups,
            all_extras=all_extras,
            all_groups=all_groups,
        )
    except (UnknownExtraError, UnknownGroupError) as exc:
        if quiet:
            print(f"Error: {exc}", file=sys.stderr)
        else:
            rprint(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc
    no_deps = (
        not selection.has_main_deps and not selection.extras and not selection.groups
    )
    if no_deps and not quiet:
        rprint(
            f"[yellow]Warning: {path} has no [project.dependencies] and "
            f"no extras/groups selected.[/yellow]"
        )
    return handle_pyproject(selection, quiet=quiet), selection


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
            help="requirements.txt, pyproject.toml or uv.lock to audit (repeatable)",
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
    discover: Annotated[
        bool,
        typer.Option("--discover", help="List dependency files instead of scanning"),
    ] = False,
    include: Annotated[
        list[str] | None,
        typer.Option("--include", help="Glob pattern to match (repeatable)"),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            help="Path component or glob pattern to skip (repeatable)",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit results as JSON to stdout"),
    ] = False,
):
    """Audit Python dependencies for known vulnerabilities.

    Accepts one or more ``requirements.txt``, ``pyproject.toml``, or
    ``uv.lock`` files (via ``-r``/``--requirement``), or a project directory
    shortcut as a positional argument.  ``requirements.txt`` and
    ``pyproject.toml`` inputs are resolved and checked against the PyPI
    vulnerability database; ``uv.lock`` files are handed to ``uv audit``.
    Findings are printed as a table and the command exits non-zero when any
    vulnerability is found.

    The ``--group``, ``--extra``, ``--all-groups``, and ``--all-extras`` flags
    control which optional dependencies are included when auditing a
    ``pyproject.toml``.  They are silently ignored for ``requirements.txt``
    and ``uv.lock`` inputs (a warning is printed in that case).
    """
    if version:
        rprint(f"[bold]uv-audit {__version__}[/bold]")
        return

    if discover:
        root = Path(project) if project else Path(".")
        if not root.exists():
            msg = f"Error: {root} does not exist."
            if json_output:
                print(msg, file=sys.stderr)
            else:
                rprint(f"[red]{msg}[/red]")
            raise typer.Exit(code=1)
        if not root.is_dir():
            msg = f"Error: {root} is not a directory."
            if json_output:
                print(msg, file=sys.stderr)
            else:
                rprint(f"[red]{msg}[/red]")
            raise typer.Exit(code=1)
        files = discover_files(
            root=root,
            includes=include or DEFAULT_INCLUDES,
            excludes=exclude or DEFAULT_EXCLUDES,
        )
        if json_output:
            print(json.dumps({"files": files}, indent=2))
        elif not files:
            rprint("[yellow]No matching files found")
        else:
            for entry in files:
                rprint(f"[bold]{entry['kind']}[/bold]  {entry['path']}")
        return

    requirements_files = requirements_files or []
    groups = groups or []
    extras = extras or []
    if all_:
        all_groups = True
        all_extras = True

    if not requirements_files and not project:
        msg = "Error: No requirements files or project directory provided."
        if json_output:
            print(msg, file=sys.stderr)
        else:
            rprint(f"[red]{msg}[/red]")
        raise typer.Exit(code=1)

    inputs: list[tuple[Path, str]] = []
    if project:
        inputs.append((Path(project) / "pyproject.toml", "pyproject"))
    inputs.extend(
        (file_path, kind_for_path(file_path)) for file_path in requirements_files
    )

    has_pyproject = any(kind == "pyproject" for _, kind in inputs)
    has_flagless_inputs = any(kind != "pyproject" for _, kind in inputs)
    selection_flags_set = bool(groups or extras or all_groups or all_extras)
    _warn_selection_flags(
        selection_flags_set, has_flagless_inputs, has_pyproject, quiet=json_output
    )

    all_vulns: list[dict] = []
    json_inputs: list[dict] = []

    for path, kind in inputs:
        if not path.exists():
            if json_output:
                print(f"Error: {path} does not exist.", file=sys.stderr)
            else:
                rprint(f"[red]Error: {path} does not exist.[/red]")
            continue
        if not path.is_file():
            if json_output:
                print(f"Error: {path} is not a file.", file=sys.stderr)
            else:
                rprint(f"[red]Error: {path} is not a file.[/red]")
            continue

        resolved_groups: list[str] = []
        resolved_extras: list[str] = []
        if kind == "pyproject":
            vulns, selection = _process_pyproject(
                path, extras, groups, all_extras, all_groups, quiet=json_output
            )
            if json_output and selection:
                resolved_groups = selection.groups
                resolved_extras = selection.extras
        elif kind == "lock":
            try:
                vulns = handle_lock(path, quiet=json_output)
            except LockAuditError as exc:
                if json_output:
                    print(f"Error: {path}: {exc}", file=sys.stderr)
                else:
                    rprint(f"[red]Error: {path}: {exc}[/red]")
                continue
        else:
            vulns = handle_file(file_path=path, is_file=True, quiet=json_output)

        all_vulns.extend(vulns)

        if json_output:
            json_inputs.append(
                {
                    "source": str(path.resolve()),
                    "kind": kind,
                    "groups": resolved_groups,
                    "extras": resolved_extras,
                    "vulnerabilities": [
                        {
                            "package": v["Name"],
                            "version": v["Version"],
                            "id": v["ID"],
                            "fix_versions": [
                                s.strip()
                                for s in v["Fix Versions"].split(",")
                                if s.strip()
                            ],
                            "link": v["Link"],
                            "aliases": v.get("Aliases", []),
                        }
                        for v in vulns
                    ],
                }
            )

    if json_output:
        payload = {
            "vulnerable": any(entry["vulnerabilities"] for entry in json_inputs),
            "inputs": json_inputs,
        }
        print(json.dumps(payload, indent=2))
        if payload["vulnerable"]:
            sys.exit(1)
        return

    if all_vulns:
        sys.exit("Vulnerabilites found")


def main():
    """Invoke the Typer application as a console-script entry point."""
    app()
