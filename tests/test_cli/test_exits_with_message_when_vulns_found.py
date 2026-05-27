from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner


def test_cli_exits_with_message_when_vulns_found(mocker: MockerFixture, tmp_path: Path):
    # arrange
    req = tmp_path / "requirements.txt"
    req.write_text("flask==1.1.2\n")
    mocker.patch(
        "uv_audit.handle_file",
        return_value=[{"Name": "flask", "Version": "1.1.2", "ID": "GHSA-1"}],
    )
    mocker.patch("uv_audit.handle_pyproject", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(req)])

    # assert
    assert result.exit_code != 0
    assert "Vulnerabilites found" in result.output
