import uuid
import subprocess
import os
import shutil


def parse_pip_list_to_requirements(pip_list_output):
    """Parst uv pip list Output zu package==version Format."""
    lines = pip_list_output.strip().split("\n")
    requirements = []

    # Überspringe Header-Zeilen (Package, ---------)
    data_started = False
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("Package") or line.startswith("-"):
            data_started = True
            continue

        if data_started and line:
            parts = line.split()
            if len(parts) >= 2:
                package = parts[0]
                version = parts[1]
                requirements.append(f"{package}=={version}")

    return requirements


class EnvironmentHandler:
    def __init__(self):
        self._folder = f"/tmp/{uuid.uuid4()}"

    @staticmethod
    def run_command(command, cwd=None):
        """Executes a shell command"""
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True, cwd=cwd
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise

    def create_venv(self):
        if os.path.exists(self._folder):
            shutil.rmtree(self._folder)

        result = self.run_command(f"uv venv {self._folder}")
        if result is not None:
            return True
        return False

    def install_requirements(self, requirements_file: str, is_file: bool = True):
        if not os.path.exists(requirements_file):
            raise Exception(f"<UNK> {requirements_file} not found.")
        if is_file:
            install_cmd = (
                f"uv pip install -r {requirements_file} --python {self._folder}"
            )
        else:
            install_cmd = f"uv pip install {requirements_file} --python {self._folder}"
        result = self.run_command(install_cmd)

        if result is not None:
            return True
        return False

    def delete_venv(self):
        if os.path.exists(self._folder):
            shutil.rmtree(self._folder)
        return True

    def list_packages(self) -> list[str]:
        list_cmd = f"uv pip list --python {self._folder}"
        result = self.run_command(list_cmd)

        if result:
            return parse_pip_list_to_requirements(result)
        return []
