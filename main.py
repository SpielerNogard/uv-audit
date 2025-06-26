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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="pip-audit like tool for auditing Python packages in requirements files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="one or more requirements files to audit (e.g. requirements.txt, requirements-dev.txt)",
    )

    args = parser.parse_args()

    for file_path in args.files:
        if not file_path.exists():
            print(f"Error: {file_path} does not exist.")
            continue

        if not file_path.is_file():
            print(f"Error: {file_path} is not a file.")
            continue

        env_handler = EnvironmentHandler()
        env_handler.create_venv()
        env_handler.install_requirements(requirements_file=file_path)
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
        print(f"Auditing {file_path} for known vulnerabilities...")
        if vulns:
            print(
                f"Found {len(vulns)} known vulnerabilities in {len(set([vuln['Name'] for vuln in vulns]))} packages"
            )
            print_simple_table(vulns)
            sys.exit(0)
        print("No known vulnerabilities found")
