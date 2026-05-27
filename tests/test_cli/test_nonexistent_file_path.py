import uv_audit
from uv_audit import app

from .conftest import runner


def test_cli_nonexistent_file_path_emits_error_and_continues(
    mocker,
):
    # arrange
    mocker.patch("uv_audit.handle_file", return_value=[])
    mocker.patch("uv_audit.handle_pyproject", return_value=[])

    # act
    result = runner.invoke(app, ["-r", "/tmp/definitely-does-not-exist-12345.txt"])

    # assert
    assert "does not exist" in result.output
    uv_audit.handle_file.assert_not_called()
    uv_audit.handle_pyproject.assert_not_called()
