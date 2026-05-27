"""Tests that a positional directory argument is treated as a pyproject.toml project."""

from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner, write_pyproject


def test_cli_positional_project_treated_as_pyproject(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify that passing a project directory as a positional argument routes to handle_pyproject."""
    # arrange
    write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n',
    )
    handle_py = mocker.patch("uv_audit.handle_pyproject", return_value=[])

    # act
    result = runner.invoke(app, [str(tmp_path)])

    # assert
    assert result.exit_code == 0, result.output
    handle_py.assert_called_once()
