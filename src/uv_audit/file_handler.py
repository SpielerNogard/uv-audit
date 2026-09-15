"""High-level orchestration of the dependency scan pipeline.

This module provides the two public entry points used by the CLI: one for
plain ``requirements.txt`` files (:func:`handle_file`), which installs into
an ephemeral venv and lists the result, and one for resolved
``pyproject.toml`` selections (:func:`handle_pyproject`), which resolves the
dependency tree with ``uv pip compile`` without building the project itself.
Both run the vulnerability scan, print a report, and return the records.

A third entry point, :func:`handle_lock`, hands ``uv.lock`` files to ``uv
audit``, which resolves and audits them natively.
"""

from pathlib import Path

from rich import print as rprint

from uv_audit.environment_handler import EnvironmentHandler, audit_lock
from uv_audit.pyproject_handler import PyProjectSelection
from uv_audit.table_view import print_simple_table
from uv_audit.vulnerability_scanner import VulnerabilityScanner

VULN_HEADERS = ["Name", "Version", "ID", "Fix Versions", "Link"]
"""Columns rendered in the terminal table; extra record keys stay hidden."""


def _print_vulns(vulns: list[dict], quiet: bool = False) -> None:
    """Print a summary table of *vulns*, or a clean-result message.

    Parameters
    ----------
    vulns : list[dict]
        Vulnerability records to display.
    quiet : bool, optional
        When ``True``, suppress all output.  Default is ``False``.
    """
    if quiet:
        return
    if vulns:
        package_count = len({v["Name"] for v in vulns})
        rprint(
            f"[red]Found {len(vulns)} known vulnerabilities in {package_count} packages"
        )
        print_simple_table(vulns, headers=VULN_HEADERS)
    else:
        rprint("[green]No known vulnerabilities found")


def _report_vulns(results: list[dict], quiet: bool = False) -> list[dict]:
    """Format and print vulnerability results, then return the flat vuln list.

    Iterates over the scanner results, flattens each package's vulnerability
    list into individual rows, prints either a Rich-coloured summary table or
    a "no vulnerabilities" message, and returns the flattened list so callers
    can decide whether to exit non-zero.

    Parameters
    ----------
    results : list[dict]
        Raw output from
        :meth:`~uv_audit.vulnerability_scanner.VulnerabilityScanner.run_check`.
        Each dict has keys ``"package"``, ``"version"``, and
        ``"vulnerabilities"`` (a list of PyPI advisory dicts).
    quiet : bool, optional
        When ``True``, suppress all output.  Default is ``False``.

    Returns
    -------
    list[dict]
        One dict per vulnerability with keys ``"Name"``, ``"Version"``,
        ``"ID"``, ``"Fix Versions"``, and ``"Link"``.  Empty list when no
        vulnerabilities were found.
    """
    vulns = [
        {
            "Name": r["package"],
            "Version": r["version"],
            "ID": v["id"],
            "Fix Versions": ", ".join(v.get("fixed_in", ["N/A"])),
            "Link": v.get("link", "N/A"),
        }
        for r in results
        for v in r["vulnerabilities"]
    ]
    _print_vulns(vulns, quiet=quiet)
    return vulns


def handle_file(
    file_path: str | Path, is_file: bool, quiet: bool = False
) -> list[dict]:
    """Audit a ``requirements.txt`` file for known vulnerabilities.

    Creates a temporary virtual environment, installs every package listed in
    *file_path*, queries the PyPI vulnerability database, and prints a summary.

    Parameters
    ----------
    file_path : str or Path
        Path to the requirements file to audit.
    is_file : bool
        When ``True``, the path is treated as a ``-r`` requirements file.
        When ``False``, it is passed as a direct package specifier to ``uv
        pip install``.
    quiet : bool, optional
        When ``True``, suppress all output.  Default is ``False``.

    Returns
    -------
    list[dict]
        Flat list of vulnerability records (see :func:`_report_vulns`).
        Empty when no vulnerabilities are found.
    """
    env_handler = EnvironmentHandler()
    env_handler.create_venv()
    env_handler.install_requirements(requirements_file=str(file_path), is_file=is_file)
    requirements = env_handler.list_packages()
    results = VulnerabilityScanner().run_check(requirements=requirements)
    env_handler.delete_venv()

    return _report_vulns(results, quiet=quiet)


def handle_pyproject(selection: PyProjectSelection, quiet: bool = False) -> list[dict]:
    """Audit a resolved ``pyproject.toml`` selection for known vulnerabilities.

    Resolves the dependencies described by *selection* with ``uv pip compile``
    (without building the project itself), queries the PyPI vulnerability
    database, and prints a summary.

    Parameters
    ----------
    selection : PyProjectSelection
        Resolved dependency selection produced by
        :func:`~uv_audit.pyproject_handler.resolve_selection`.
    quiet : bool, optional
        When ``True``, suppress all output.  Default is ``False``.

    Returns
    -------
    list[dict]
        Flat list of vulnerability records (see :func:`_report_vulns`).
        Empty when no vulnerabilities are found or no installable dependencies
        exist.
    """
    has_selection = selection.has_main_deps or selection.extras or selection.groups
    if has_selection:
        requirements = EnvironmentHandler().compile_pyproject(selection)
    else:
        requirements = []

    if not requirements:
        if not quiet:
            rprint("[yellow]No installable dependencies found in pyproject.toml")
        return []

    results = VulnerabilityScanner().run_check(requirements=requirements)

    return _report_vulns(results, quiet=quiet)


def handle_lock(lock_path: str | Path, quiet: bool = False) -> list[dict]:
    """Audit a ``uv.lock`` file for known vulnerabilities via ``uv audit``.

    Unlike the other entry points this creates no environment and performs no
    PyPI lookups — ``uv audit`` reads the lockfile and queries its own
    vulnerability service.  The ``--group``/``--extra`` selection flags do not
    apply; see :func:`~uv_audit.environment_handler.audit_lock`.

    Parameters
    ----------
    lock_path : str or Path
        Path to the ``uv.lock`` file to audit.
    quiet : bool, optional
        When ``True``, suppress all output.  Default is ``False``.

    Returns
    -------
    list[dict]
        Flat list of vulnerability records (see :func:`_report_vulns`), each
        additionally carrying an ``"Aliases"`` key.  Empty when no
        vulnerabilities are found.

    Raises
    ------
    ~uv_audit.environment_handler.LockAuditError
        When ``uv audit`` fails or emits output that cannot be read.
    """
    vulns = audit_lock(lock_path)
    _print_vulns(vulns, quiet=quiet)
    return vulns
