"""Tests that passing a directory path to -r is rejected with an appropriate error message."""

from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner


def test_cli_directory_path_as_dash_r_emits_not_a_file_error(
    mocker: MockerFixture, tmp_path: Path
):
    """Ensure the CLI prints an 'is not a file' error when a directory is passed via -r."""
    # arrange
    mocker.patch("uv_audit.handle_file", return_value=[])
    mocker.patch("uv_audit.handle_pyproject", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(tmp_path)])

    # assert
    assert "is not a file" in result.output
