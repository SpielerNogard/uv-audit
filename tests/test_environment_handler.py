import subprocess
import uuid
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from uv_audit.environment_handler import (
    EnvironmentHandler,
    parse_pip_list_to_requirements,
)
from uv_audit.pyproject_handler import PyProjectSelection


def test_install_pyproject_builds_command_with_extras_and_groups(
    mocker: MockerFixture, tmp_path: Path
):
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


# ---------------------------------------------------------------------------
# parse_pip_list_to_requirements
# ---------------------------------------------------------------------------


def test_parse_pip_list_to_requirements_typical_output():
    # arrange
    pip_list_output = (
        "Package    Version\n---------- -------\nclick      8.2.1\nrequests   2.32.3\n"
    )

    # act
    result = parse_pip_list_to_requirements(pip_list_output)

    # assert
    assert result == ["click==8.2.1", "requests==2.32.3"]


def test_parse_pip_list_to_requirements_empty_input():
    # act
    result = parse_pip_list_to_requirements("")

    # assert
    assert result == []


def test_parse_pip_list_to_requirements_skips_blank_and_short_lines():
    # arrange
    pip_list_output = (
        "Package    Version\n"
        "---------- -------\n"
        "\n"
        "click      8.2.1\n"
        "badline\n"
        "requests   2.32.3\n"
    )

    # act
    result = parse_pip_list_to_requirements(pip_list_output)

    # assert
    assert result == ["click==8.2.1", "requests==2.32.3"]


# ---------------------------------------------------------------------------
# EnvironmentHandler.__init__
# ---------------------------------------------------------------------------


def test_environment_handler_init_folder_uses_tmp_prefix_and_uuid():
    # arrange / act
    handler = EnvironmentHandler()

    # assert
    assert handler._folder.startswith("/tmp/")
    suffix = handler._folder.removeprefix("/tmp/")
    uuid.UUID(suffix)  # raises ValueError if not a valid UUID


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------


def test_run_command_success(mocker: MockerFixture):
    # arrange
    mock_result = mocker.MagicMock()
    mock_result.stdout = "hello\n"
    mock_run = mocker.patch(
        "uv_audit.environment_handler.subprocess.run", return_value=mock_result
    )

    # act
    result = EnvironmentHandler.run_command("echo hello")

    # assert
    assert result == "hello"
    mock_run.assert_called_once_with(
        "echo hello",
        shell=True,
        check=True,
        capture_output=True,
        text=True,
        cwd=None,
    )


def test_run_command_failure_reraises(mocker: MockerFixture):
    # arrange
    mocker.patch(
        "uv_audit.environment_handler.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "x"),
    )

    # act / assert
    with pytest.raises(subprocess.CalledProcessError):
        EnvironmentHandler.run_command("bad-command")


# ---------------------------------------------------------------------------
# create_venv
# ---------------------------------------------------------------------------


def test_create_venv_when_folder_does_not_exist(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=False)
    run = mocker.patch.object(handler, "run_command", return_value="ok")

    # act
    result = handler.create_venv()

    # assert
    run.assert_called_once_with(f"uv venv {handler._folder}")
    assert result is True


def test_create_venv_when_folder_exists_calls_rmtree_first(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=True)
    rmtree = mocker.patch("uv_audit.environment_handler.shutil.rmtree")
    run = mocker.patch.object(handler, "run_command", return_value="ok")

    # act
    result = handler.create_venv()

    # assert
    rmtree.assert_called_once_with(handler._folder)
    run.assert_called_once_with(f"uv venv {handler._folder}")
    assert result is True


# ---------------------------------------------------------------------------
# install_requirements
# ---------------------------------------------------------------------------


def test_install_requirements_raises_when_file_missing(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=False)

    # act / assert
    with pytest.raises(Exception, match="not found"):
        handler.install_requirements("/nonexistent")


def test_install_requirements_is_file_true(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=True)
    run = mocker.patch.object(handler, "run_command", return_value="ok")

    # act
    result = handler.install_requirements("/req.txt", is_file=True)

    # assert
    run.assert_called_once_with(
        f"uv pip install -r /req.txt --python {handler._folder}"
    )
    assert result is True


def test_install_requirements_is_file_false(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=True)
    run = mocker.patch.object(handler, "run_command", return_value="ok")

    # act
    result = handler.install_requirements("/some/path", is_file=False)

    # assert
    run.assert_called_once_with(f"uv pip install /some/path --python {handler._folder}")
    assert result is True


# ---------------------------------------------------------------------------
# delete_venv
# ---------------------------------------------------------------------------


def test_delete_venv_when_folder_exists(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=True)
    rmtree = mocker.patch("uv_audit.environment_handler.shutil.rmtree")

    # act
    result = handler.delete_venv()

    # assert
    assert result is True
    rmtree.assert_called_once_with(handler._folder)


def test_delete_venv_when_folder_does_not_exist(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=False)
    rmtree = mocker.patch("uv_audit.environment_handler.shutil.rmtree")

    # act
    result = handler.delete_venv()

    # assert
    assert result is True
    rmtree.assert_not_called()


# ---------------------------------------------------------------------------
# list_packages
# ---------------------------------------------------------------------------


def test_list_packages_returns_empty_list_when_no_output(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    mocker.patch.object(handler, "run_command", return_value="")

    # act
    result = handler.list_packages()

    # assert
    assert result == []


def test_list_packages_returns_parsed_packages(mocker: MockerFixture):
    # arrange
    handler = EnvironmentHandler()
    pip_output = (
        "Package    Version\n---------- -------\nclick      8.2.1\nrequests   2.32.3\n"
    )
    mocker.patch.object(handler, "run_command", return_value=pip_output)

    # act
    result = handler.list_packages()

    # assert
    assert result == ["click==8.2.1", "requests==2.32.3"]
