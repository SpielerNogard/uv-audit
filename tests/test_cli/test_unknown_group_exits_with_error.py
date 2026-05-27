from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner, write_pyproject


def test_cli_unknown_group_exits_with_error(mocker: MockerFixture, tmp_path: Path):
    # arrange
    pyproject = write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n'
        '\n[dependency-groups]\ndev=["pytest"]\n',
    )
    mocker.patch("uv_audit.handle_pyproject", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(pyproject), "--group", "missing"])

    # assert
    assert result.exit_code != 0
    assert "missing" in result.output
    assert "dev" in result.output
