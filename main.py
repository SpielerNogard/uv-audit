# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "uv-audit @ git+https://github.com/SpielerNogard/uv-audit.git@main"
# ]
# ///

from uv_audit.environment_handler import EnvironmentHandler
from uv_audit.vulnerability_scanner import VulnerabilityScanner
import argparse
from uv_audit.table_view import print_simple_table
from pathlib import Path
import sys


def _handle_file(file_path: str, is_file: bool):
    env_handler = EnvironmentHandler()
    env_handler.create_venv()
    env_handler.install_requirements(requirements_file=file_path, is_file=is_file)
    requirements = env_handler.list_packages()
    results = VulnerabilityScanner().run_check(requirements=requirements)
    env_handler.delete_venv()

    vulns = []
    for result in results:
        for vuln in result["vulnerabilities"]:
            vulns.append(
                {
                    "Name": result["package"],
                    "Version": result["version"],
                    "ID": vuln["id"],
                    "Fix Versions": ", ".join(vuln.get("fixed_in", ["N/A"])),
                    "Link": vuln.get("link", "N/A"),
                }
            )
    # print(vulns)
    # print(f"Auditing {file_path} for known vulnerabilities...")
    if vulns:
        print(
            f"Found {len(vulns)} known vulnerabilities in {len(set([vuln['Name'] for vuln in vulns]))} packages"
        )
        print_simple_table(vulns)
        return vulns
    print("No known vulnerabilities found")
    return vulns


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="pip-audit like tool for auditing Python packages in requirements files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-r",
        "--requirement",
        dest="requirements_files",
        action="append",
        type=Path,
        default=[],
        help="requirements file to audit (can be used multiple times: -r requirements.txt -r requirements-dev.txt)",
    )

    parser.add_argument(
        "project",
        nargs="?",
        help="optional argument (e.g. directory path)",
    )

    args = parser.parse_args()
    if not args.requirements_files and not args.project:
        print("Error: No requirements files or project directory provided.")
        sys.exit(1)

    if args.project:
        _handle_file(args.project, False)

    for file_path in args.requirements_files:
        if not file_path.exists():
            print(f"Error: {file_path} does not exist.")
            continue

        if not file_path.is_file():
            print(f"Error: {file_path} is not a file.")
            continue
        _handle_file(file_path=file_path, is_file=True)

    # md_view.to_file("test.md")
