"""Tests for EnvironmentHandler.compile_pyproject, covering extras, groups, and parsing."""

from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit.environment_handler import EnvironmentHandler
from uv_audit.pyproject_handler import PyProjectSelection


def test_compile_pyproject_builds_command_with_extras_and_groups(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify that extras and groups become --extra/--group flags and the parsed result is returned."""
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
    run = mocker.patch.object(
        handler,
        "run_command",
        return_value="requests==2.32.3\n    # via x\n",
    )

    # act
    result = handler.compile_pyproject(selection)

    # assert
    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert cmd.startswith(f"uv pip compile {pyproject} ")
    assert "--extra cli" in cmd
    assert "--extra ml" in cmd
    assert f"--group {pyproject}:dev" in cmd
    assert f"--group {pyproject}:test" in cmd
    assert "--no-header" in cmd
    assert result == ["requests==2.32.3"]


def test_compile_pyproject_no_extras_no_groups(mocker: MockerFixture, tmp_path: Path):
    """Verify that the compile command has no --extra or --group flags when none are selected."""
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
    run = mocker.patch.object(handler, "run_command", return_value="")

    # act
    result = handler.compile_pyproject(selection)

    # assert
    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert cmd.startswith(f"uv pip compile {pyproject} ")
    assert "--extra" not in cmd
    assert "--group" not in cmd
    assert result == []
