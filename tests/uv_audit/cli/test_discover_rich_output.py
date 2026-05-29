"""Tests that --discover without --json renders a Rich-formatted listing to stdout."""

from pathlib import Path

from uv_audit import app

from .conftest import runner


def test_cli_discover_rich_lists_files(tmp_path: Path):
    """Verify --discover (no --json) prints each discovered file as 'kind  path'."""
    # arrange
    (tmp_path / "pyproject.toml").write_text("")

    # act
    result = runner.invoke(app, ["--discover", str(tmp_path)])

    # assert
    assert result.exit_code == 0
    assert "pyproject" in result.output
    assert "pyproject.toml" in result.output
