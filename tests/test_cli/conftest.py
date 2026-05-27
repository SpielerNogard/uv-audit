from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()


def write_pyproject(path: Path, body: str) -> Path:
    p = path / "pyproject.toml"
    p.write_text(body)
    return p
