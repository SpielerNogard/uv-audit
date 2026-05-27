"""Shared fixtures and helpers for the CLI test suite."""

from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()
"""Typer ``CliRunner`` instance shared across all CLI tests."""


def write_pyproject(path: Path, body: str) -> Path:
    """Write a pyproject.toml under ``path`` and return its full path.

    Parameters
    ----------
    path : Path
        Directory in which to create the file.
    body : str
        TOML content to write.

    Returns
    -------
    Path
        Absolute path to the newly written file.
    """
    p = path / "pyproject.toml"
    p.write_text(body)
    return p
