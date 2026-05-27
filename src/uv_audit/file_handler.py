from pathlib import Path

from rich import print as rprint

from uv_audit.environment_handler import EnvironmentHandler
from uv_audit.pyproject_handler import PyProjectSelection
from uv_audit.table_view import print_simple_table
from uv_audit.vulnerability_scanner import VulnerabilityScanner


def _report_vulns(results: list[dict]) -> list[dict]:
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
    env_handler = EnvironmentHandler()
    env_handler.create_venv()
    env_handler.install_requirements(requirements_file=str(file_path), is_file=is_file)
    requirements = env_handler.list_packages()
    results = VulnerabilityScanner().run_check(requirements=requirements)
    env_handler.delete_venv()

    return _report_vulns(results)


def handle_pyproject(selection: PyProjectSelection) -> list[dict]:
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
