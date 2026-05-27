"""Tests that a pyproject.toml path passed via -r is routed to handle_pyproject, not handle_file."""

from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner, write_pyproject


def test_cli_routes_pyproject_through_handle_pyproject(
    mocker: MockerFixture, tmp_path: Path
):
    """Ensure a pyproject.toml file is dispatched to handle_pyproject and not handle_file."""
    # arrange
    pyproject = write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n',
    )
    handle_py = mocker.patch("uv_audit.handle_pyproject", return_value=[])
    handle_file_fn = mocker.patch("uv_audit.handle_file", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(pyproject)])

    # assert
    assert result.exit_code == 0, result.output
    handle_py.assert_called_once()
    handle_file_fn.assert_not_called()
