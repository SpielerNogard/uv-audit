# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "aiohttp",
# ]
# ///

from uv_audit.environment_handler import EnvironmentHandler
from uv_audit.vulnerability_scanner import VulnerabilityScanner
import argparse
from uv_audit.table_view import print_simple_table
from pathlib import Path
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='pip-audit like tool for auditing Python packages in requirements files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='one or more requirements files to audit (e.g. requirements.txt, requirements-dev.txt)',
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
                vulns.append({"package": result["package"], "version": result["version"], "vulnerability": vuln["id"], "fixed_in": vuln.get("fixed_in", "N/A"), "link": vuln.get("link", "N/A")})

        print_simple_table(vulns)


