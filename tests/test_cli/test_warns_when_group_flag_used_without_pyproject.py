from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner


def test_cli_warns_when_group_flag_used_without_pyproject(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.32.3\n")
    mocker.patch("uv_audit.handle_file", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(req), "--group", "dev"])

    # assert
    assert result.exit_code == 0, result.output
    assert "ignored" in result.output.lower() or "warning" in result.output.lower()
