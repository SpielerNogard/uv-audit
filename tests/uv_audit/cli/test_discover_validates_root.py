"""Tests that --discover validates that the discovery root is an existing directory."""

from pathlib import Path

from uv_audit import app

from .conftest import runner


def test_discover_rejects_nonexistent_root(tmp_path: Path):
    """Confirm --discover prints a clear error and exits non-zero when the root path is missing."""
    # arrange
    missing = tmp_path / "does-not-exist"

    # act
    result = runner.invoke(app, ["--discover", str(missing)])

    # assert
    assert result.exit_code != 0
    assert "does not exist" in result.output or "is not a directory" in result.output


def test_discover_rejects_file_as_root(tmp_path: Path):
    """Confirm --discover rejects a file (not directory) as the discovery root."""
    # arrange
    file_path = tmp_path / "some_file.txt"
    file_path.write_text("")

    # act
    result = runner.invoke(app, ["--discover", str(file_path)])

    # assert
    assert result.exit_code != 0
    assert "is not a directory" in result.output
