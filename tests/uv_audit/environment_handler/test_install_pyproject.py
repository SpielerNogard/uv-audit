"""Tests for EnvironmentHandler.install_pyproject, covering extras, groups, and the no-selection case."""

from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit.environment_handler import EnvironmentHandler
from uv_audit.pyproject_handler import PyProjectSelection


def test_install_pyproject_builds_command_with_extras_and_groups(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify that extras and groups are appended to the uv pip install command in the correct format."""
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'x'\nversion = '0.0.0'\n")
    selection = PyProjectSelection(
        path=pyproject,
        extras=["cli", "ml"],
        groups=["dev", "test"],
        has_main_deps=True,
    )
    handler = EnvironmentHandler()
    run = mocker.patch.object(handler, "run_command", return_value="ok")

    # act
    result = handler.install_pyproject(selection)

    # assert
    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert result is True
    assert f"{tmp_path}[cli,ml]" in cmd
    assert f"--group {pyproject}:dev" in cmd
    assert f"--group {pyproject}:test" in cmd
    assert f"--python {handler._folder}" in cmd


def test_install_pyproject_no_extras_no_groups(mocker: MockerFixture, tmp_path: Path):
    """Verify that the install command has no brackets or --group flags when selection has no extras or groups."""
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'x'\nversion = '0.0.0'\n")
    selection = PyProjectSelection(
        path=pyproject,
        extras=[],
        groups=[],
        has_main_deps=True,
    )
    handler = EnvironmentHandler()
    run = mocker.patch.object(handler, "run_command", return_value="ok")

    # act
    result = handler.install_pyproject(selection)

    # assert
    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert result is True
    assert f"uv pip install {tmp_path} " in cmd
    assert "[" not in cmd
    assert "--group" not in cmd
