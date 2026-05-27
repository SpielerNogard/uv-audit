from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner, write_pyproject


def test_cli_mixed_inputs_warns_and_dispatches_both(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.32.3\n")
    pyproject = write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n'
        '\n[dependency-groups]\ndev=["pytest"]\n',
    )
    handle_py = mocker.patch("uv_audit.handle_pyproject", return_value=[])
    handle_file_fn = mocker.patch("uv_audit.handle_file", return_value=[])

    # act
    result = runner.invoke(
        app, ["-r", str(req), "-r", str(pyproject), "--group", "dev"]
    )

    # assert
    assert result.exit_code == 0, result.output
    handle_py.assert_called_once()
    handle_file_fn.assert_called_once()
    assert "apply only to pyproject.toml" in result.output.lower()
