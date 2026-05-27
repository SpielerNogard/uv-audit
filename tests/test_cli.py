from pathlib import Path

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from uv_audit import app

runner = CliRunner()


def _write_pyproject(path: Path, body: str) -> Path:
    p = path / "pyproject.toml"
    p.write_text(body)
    return p


def test_cli_routes_pyproject_through_handle_pyproject(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    pyproject = _write_pyproject(
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


def test_cli_positional_project_treated_as_pyproject(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    _write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n',
    )
    handle_py = mocker.patch("uv_audit.handle_pyproject", return_value=[])

    # act
    result = runner.invoke(app, [str(tmp_path)])

    # assert
    assert result.exit_code == 0, result.output
    handle_py.assert_called_once()


def test_cli_unknown_group_exits_with_error(mocker: MockerFixture, tmp_path: Path):
    # arrange
    pyproject = _write_pyproject(
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


def test_cli_all_flag_implies_all_groups_and_all_extras(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    pyproject = _write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n'
        '\n[project.optional-dependencies]\ncli=["click"]\n'
        '\n[dependency-groups]\ndev=["pytest"]\n',
    )
    captured = {}

    def fake_handle(selection):
        captured["selection"] = selection
        return []

    mocker.patch("uv_audit.handle_pyproject", side_effect=fake_handle)

    # act
    result = runner.invoke(app, ["-r", str(pyproject), "--all"])

    # assert
    assert result.exit_code == 0, result.output
    assert captured["selection"].extras == ["cli"]
    assert captured["selection"].groups == ["dev"]


def test_cli_mixed_inputs_warns_and_dispatches_both(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.32.3\n")
    pyproject = _write_pyproject(
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
