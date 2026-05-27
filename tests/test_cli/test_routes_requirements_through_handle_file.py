from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner


def test_cli_routes_requirements_through_handle_file(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.32.3\n")
    handle_py = mocker.patch("uv_audit.handle_pyproject", return_value=[])
    handle_file_fn = mocker.patch("uv_audit.handle_file", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(req)])

    # assert
    assert result.exit_code == 0, result.output
    handle_file_fn.assert_called_once()
    handle_py.assert_not_called()
