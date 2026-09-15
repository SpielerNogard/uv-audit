"""Ephemeral virtual-environment lifecycle management using ``uv``.

This module creates a throw-away ``uv`` virtual environment under ``/tmp``,
installs the requested dependencies into it, lists the installed packages in
``package==version`` format, and deletes the environment afterwards.

It also wraps ``uv audit``, which audits a ``uv.lock`` natively and needs no
environment at all.
"""

import json
import os
import shlex
import shutil
import subprocess
import uuid
from pathlib import Path

from uv_audit.pyproject_handler import PyProjectSelection

AUDIT_EXIT_CODES = (0, 1)
"""``uv audit`` exit codes that carry a report: 0 is clean, 1 means findings."""


class LockAuditError(RuntimeError):
    """Raised when ``uv audit`` fails or emits output we cannot read."""


def _to_record(vulnerability: dict) -> dict:
    """Convert one ``uv audit`` finding into a uv-audit vulnerability record.

    Parameters
    ----------
    vulnerability : dict
        A single entry from the ``vulnerabilities`` array of ``uv audit
        --output-format json``.

    Returns
    -------
    dict
        Record with the keys ``"Name"``, ``"Version"``, ``"ID"``,
        ``"Fix Versions"``, ``"Link"``, and ``"Aliases"``.

    Examples
    --------
    >>> record = _to_record(
    ...     {
    ...         "dependency": {"name": "flask", "version": "1.1.2"},
    ...         "display_id": "GHSA-1",
    ...         "aliases": ["CVE-2023-30861"],
    ...         "fix_versions": ["2.2.5"],
    ...     }
    ... )
    >>> record["Name"], record["ID"], record["Fix Versions"], record["Link"]
    ('flask', 'GHSA-1', '2.2.5', 'N/A')
    """
    dependency = vulnerability["dependency"]
    return {
        "Name": dependency["name"],
        "Version": dependency["version"],
        "ID": vulnerability["display_id"],
        "Fix Versions": ", ".join(vulnerability.get("fix_versions") or ["N/A"]),
        "Link": vulnerability.get("link") or "N/A",
        "Aliases": vulnerability.get("aliases", []),
    }


def _deduplicate(records: list[dict]) -> list[dict]:
    """Drop records that repeat an advisory already seen for the same package.

    ``uv audit`` lists an advisory once per identifier it is known by, so the
    same finding arrives as both ``GHSA-…`` and ``PYSEC-…``.  The first record
    of each group wins; the dropped identifiers survive in its ``"Aliases"``.

    Parameters
    ----------
    records : list[dict]
        Vulnerability records in the order ``uv audit`` reported them.

    Returns
    -------
    list[dict]
        The records with alias duplicates removed, order preserved.

    Examples
    --------
    >>> ghsa = {"Name": "flask", "ID": "GHSA-1", "Aliases": ["PYSEC-2"]}
    >>> pysec = {"Name": "flask", "ID": "PYSEC-2", "Aliases": ["GHSA-1"]}
    >>> [record["ID"] for record in _deduplicate([ghsa, pysec])]
    ['GHSA-1']
    """
    seen: set[tuple[str, str]] = set()
    unique = []
    for record in records:
        identifiers = {(record["Name"], i) for i in (record["ID"], *record["Aliases"])}
        if identifiers & seen:
            continue
        seen |= identifiers
        unique.append(record)
    return unique


def audit_lock(lock_path: str | Path) -> list[dict]:
    """Audit a ``uv.lock`` with ``uv audit`` and return vulnerability records.

    Runs ``uv audit --frozen`` in the lock file's directory, so the lockfile is
    read as-is and never re-resolved. The ``--group``/``--extra`` selection
    flags are not forwarded: ``uv audit`` offers no include-style equivalents,
    and auditing its default selection (main dependencies, default groups, all
    extras) is the closest honest match.

    Parameters
    ----------
    lock_path : str or Path
        Path to the ``uv.lock`` file to audit.

    Returns
    -------
    list[dict]
        One record per finding (see :func:`_to_record`). Advisories that
        ``uv audit`` reports under several identifiers are collapsed into a
        single record (see :func:`_deduplicate`). Empty when the project is
        clean.

    Raises
    ------
    LockAuditError
        When ``uv audit`` exits with anything other than 0 or 1, or when its
        output cannot be read. The JSON schema is marked ``preview`` upstream,
        so shape changes surface here as a readable error.
    """
    directory = Path(lock_path).parent
    command = (
        f"uv audit --frozen --output-format json "
        f"--directory {shlex.quote(str(directory))}"
    )
    completed = subprocess.run(
        command, shell=True, capture_output=True, text=True, check=False
    )
    if completed.returncode not in AUDIT_EXIT_CODES:
        detail = (
            completed.stderr.strip() or f"uv audit exited with {completed.returncode}"
        )
        raise LockAuditError(detail)

    try:
        payload = json.loads(completed.stdout)
        records = [_to_record(v) for v in payload["vulnerabilities"]]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise LockAuditError(f"unexpected `uv audit` output: {exc}") from exc

    return _deduplicate(records)


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


def parse_compile_to_requirements(compile_output: str) -> list[str]:
    """Convert ``uv pip compile`` output to a list of ``package==version`` strings.

    ``uv pip compile`` writes one ``<package>==<version>`` line per resolved
    package, optionally followed by indented ``# via ...`` annotation lines and
    an autogenerated header comment.  This function discards blank lines, full
    comment lines, and trailing ``# ...`` comments to yield the pinned
    requirements list.

    Parameters
    ----------
    compile_output : str
        Raw stdout captured from ``uv pip compile``.

    Returns
    -------
    list[str]
        Each element is a ``"package==version"`` string, one per resolved
        package.
    """
    requirements = []
    for line in compile_output.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        spec = stripped.split("#", 1)[0].strip()
        if "==" in spec:
            requirements.append(spec)
    return requirements


class EnvironmentHandler:
    """Manage a temporary ``uv`` virtual environment for dependency auditing.

    Each instance owns exactly one environment directory under ``/tmp``,
    identified by a random UUID.  The typical usage pattern is:

    1. :meth:`create_venv` — create the isolated environment.
    2. :meth:`install_requirements` — populate it.
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

    def compile_pyproject(self, selection: PyProjectSelection) -> list[str]:
        """Resolve a ``pyproject.toml`` selection into pinned requirements.

        Runs ``uv pip compile`` against the project's ``pyproject.toml`` with
        the requested extras and dependency groups.  The project itself is
        never built — only the dependency tree is resolved — so projects that
        are not installable as a wheel (e.g. flat-layout setuptools projects
        with multiple top-level packages) can still be audited.

        Parameters
        ----------
        selection : PyProjectSelection
            Resolved selection produced by
            :func:`~uv_audit.pyproject_handler.resolve_selection`.

        Returns
        -------
        list[str]
            Each element is a ``"package==version"`` string covering the full
            transitive dependency tree.  Empty when nothing resolves.
        """
        parts = [
            f"uv pip compile {shlex.quote(str(selection.path))} --no-header --quiet"
        ]
        parts.extend(f"--extra {shlex.quote(extra)}" for extra in selection.extras)
        parts.extend(
            f"--group {shlex.quote(f'{selection.path}:{group}')}"
            for group in selection.groups
        )

        output = self.run_command(" ".join(parts))
        return parse_compile_to_requirements(output) if output else []

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
