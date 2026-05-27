"""Tests for EnvironmentHandler.run_command, verifying subprocess invocation and error propagation."""

import subprocess

import pytest
from pytest_mock import MockerFixture

from uv_audit.environment_handler import EnvironmentHandler


def test_run_command_success(mocker: MockerFixture):
    """Verify run_command invokes subprocess.run with shell=True and returns the stripped stdout."""
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
    """Ensure run_command re-raises CalledProcessError when subprocess.run fails."""
    # arrange
    mocker.patch(
        "uv_audit.environment_handler.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "x"),
    )

    # act / assert
    with pytest.raises(subprocess.CalledProcessError):
        EnvironmentHandler.run_command("bad-command")
