"""High-level orchestration of the install-then-scan pipeline.

This module provides the two public entry points used by the CLI: one for
plain ``requirements.txt`` files (:func:`handle_file`) and one for resolved
``pyproject.toml`` selections (:func:`handle_pyproject`).  Both functions
create an ephemeral virtual environment, install dependencies, run the
vulnerability scan, print a report, and return the vulnerability records.
"""

from pathlib import Path

from rich import print as rprint

from uv_audit.environment_handler import EnvironmentHandler
from uv_audit.pyproject_handler import PyProjectSelection
from uv_audit.table_view import print_simple_table
from uv_audit.vulnerability_scanner import VulnerabilityScanner


def _report_vulns(results: list[dict]) -> list[dict]:
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
    if vulns:
        package_count = len({v["Name"] for v in vulns})
        rprint(
            f"[red]Found {len(vulns)} known vulnerabilities in {package_count} packages"
        )
        print_simple_table(vulns)
    else:
        rprint("[green]No known vulnerabilities found")
    return vulns


def handle_file(file_path: str | Path, is_file: bool) -> list[dict]:
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

    return _report_vulns(results)


def handle_pyproject(selection: PyProjectSelection) -> list[dict]:
    """Audit a resolved ``pyproject.toml`` selection for known vulnerabilities.

    Creates a temporary virtual environment, installs the dependencies
    described by *selection* (skipping installation when there is nothing to
    install), queries the PyPI vulnerability database, and prints a summary.

    Parameters
    ----------
    selection : PyProjectSelection
        Resolved dependency selection produced by
        :func:`~uv_audit.pyproject_handler.resolve_selection`.

    Returns
    -------
    list[dict]
        Flat list of vulnerability records (see :func:`_report_vulns`).
        Empty when no vulnerabilities are found or no installable dependencies
        exist.
    """
    env_handler = EnvironmentHandler()
    env_handler.create_venv()

    should_install = selection.has_main_deps or selection.extras or selection.groups
    if should_install:
        env_handler.install_pyproject(selection)

    requirements = env_handler.list_packages()
    env_handler.delete_venv()

    if not requirements:
        rprint("[yellow]No installable dependencies found in pyproject.toml")
        return []

    results = VulnerabilityScanner().run_check(requirements=requirements)

    return _report_vulns(results)
