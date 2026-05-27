"""Ephemeral virtual-environment lifecycle management using ``uv``.

This module creates a throw-away ``uv`` virtual environment under ``/tmp``,
installs the requested dependencies into it, lists the installed packages in
``package==version`` format, and deletes the environment afterwards.
"""

import os
import shlex
import shutil
import subprocess
import uuid

from uv_audit.pyproject_handler import PyProjectSelection


def parse_pip_list_to_requirements(pip_list_output):
    """Convert ``uv pip list`` output to a list of ``package==version`` strings.

    The ``uv pip list`` output contains a two-line header (column names and a
    separator made of dashes) followed by one ``<package>  <version>`` row per
    installed package.  This function strips that header and normalises each
    data row into the ``package==version`` format expected by
    :class:`VulnerabilityScanner`.

    Parameters
    ----------
    pip_list_output : str
        Raw stdout captured from ``uv pip list``.

    Returns
    -------
    list[str]
        Each element is a ``"package==version"`` string, one per installed
        package.

    Examples
    --------
    >>> output = "Package    Version\\n---------- -------\\nrequests   2.32.3"
    >>> parse_pip_list_to_requirements(output)
    ['requests==2.32.3']
    >>> parse_pip_list_to_requirements("")
    []
    """
    lines = pip_list_output.strip().split("\n")
    requirements = []

    data_started = False
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith(("Package", "-")):
            data_started = True
            continue

        if data_started and line:
            match line.split():
                case [package, version, *_]:
                    requirements.append(f"{package}=={version}")

    return requirements


class EnvironmentHandler:
    """Manage a temporary ``uv`` virtual environment for dependency auditing.

    Each instance owns exactly one environment directory under ``/tmp``,
    identified by a random UUID.  The typical usage pattern is:

    1. :meth:`create_venv` — create the isolated environment.
    2. :meth:`install_requirements` or :meth:`install_pyproject` — populate it.
    3. :meth:`list_packages` — enumerate installed packages.
    4. :meth:`delete_venv` — clean up.
    """

    def __init__(self):
        """Initialise the handler with a unique temporary directory path."""
        self._folder = f"/tmp/{uuid.uuid4()}"

    @staticmethod
    def run_command(command, cwd=None):
        """Execute a shell command and return its stdout.

        Parameters
        ----------
        command : str
            Shell command string to run.
        cwd : str or None, optional
            Working directory for the subprocess (default: inherited from the
            current process).

        Returns
        -------
        str
            Stripped standard output of the completed command.

        Raises
        ------
        subprocess.CalledProcessError
            When the command exits with a non-zero return code.
        """
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True, cwd=cwd
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise

    def create_venv(self):
        """Create the temporary virtual environment, replacing any existing one.

        Returns
        -------
        bool
            ``True`` when the ``uv venv`` command succeeds.
        """
        if os.path.exists(self._folder):
            shutil.rmtree(self._folder)

        result = self.run_command(f"uv venv {self._folder}")
        return result is not None

    def install_requirements(self, requirements_file: str, is_file: bool = True):
        """Install packages from a requirements file or a direct specifier.

        Parameters
        ----------
        requirements_file : str
            Path to a requirements file (when *is_file* is ``True``) or a
            direct package specifier string (when *is_file* is ``False``).
        is_file : bool, optional
            When ``True`` (default), pass *requirements_file* via ``-r``.
            When ``False``, install it as a bare package specifier.

        Returns
        -------
        bool
            ``True`` when installation succeeds.

        Raises
        ------
        Exception
            When *requirements_file* does not exist on disk.
        """
        if not os.path.exists(requirements_file):
            raise Exception(f"<UNK> {requirements_file} not found.")
        if is_file:
            install_cmd = (
                f"uv pip install -r {requirements_file} --python {self._folder}"
            )
        else:
            install_cmd = f"uv pip install {requirements_file} --python {self._folder}"
        result = self.run_command(install_cmd)
        return result is not None

    def install_pyproject(self, selection: PyProjectSelection) -> bool:
        """Install dependencies declared in a ``pyproject.toml`` selection.

        Builds a ``uv pip install`` command that targets the project directory
        (with optional extras appended in bracket notation) and adds
        ``--group`` flags for each requested dependency group.

        Parameters
        ----------
        selection : PyProjectSelection
            Resolved selection produced by
            :func:`~uv_audit.pyproject_handler.resolve_selection`.

        Returns
        -------
        bool
            ``True`` when installation succeeds.
        """
        target_dir = selection.path.parent
        target = str(target_dir)
        if selection.extras:
            target += f"[{','.join(selection.extras)}]"

        parts = [f"uv pip install {shlex.quote(target)} --python {self._folder}"]
        parts.extend(
            f"--group {shlex.quote(f'{selection.path}:{group}')}"
            for group in selection.groups
        )

        result = self.run_command(" ".join(parts))
        return result is not None

    def delete_venv(self):
        """Remove the temporary virtual environment from disk.

        Returns
        -------
        bool
            Always ``True``.
        """
        if os.path.exists(self._folder):
            shutil.rmtree(self._folder)
        return True

    def list_packages(self) -> list[str]:
        """List all packages installed in the virtual environment.

        Returns
        -------
        list[str]
            Each element is a ``"package==version"`` string.  Returns an empty
            list when no packages are installed or the command produces no
            output.
        """
        list_cmd = f"uv pip list --python {self._folder}"
        result = self.run_command(list_cmd)

        if result:
            return parse_pip_list_to_requirements(result)
        return []
