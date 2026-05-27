"""Tests for EnvironmentHandler.install_requirements, covering missing files and the is_file flag."""

import pytest
from pytest_mock import MockerFixture

from uv_audit.environment_handler import EnvironmentHandler


def test_install_requirements_raises_when_file_missing(mocker: MockerFixture):
    """Ensure install_requirements raises an exception containing 'not found' when the path does not exist."""
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=False)

    # act / assert
    with pytest.raises(Exception, match="not found"):
        handler.install_requirements("/nonexistent")


def test_install_requirements_is_file_true(mocker: MockerFixture):
    """Verify that is_file=True produces a 'uv pip install -r <path>' command."""
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
    """Verify that is_file=False produces a 'uv pip install <path>' command without the -r flag."""
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=True)
    run = mocker.patch.object(handler, "run_command", return_value="ok")

    # act
    result = handler.install_requirements("/some/path", is_file=False)

    # assert
    run.assert_called_once_with(f"uv pip install /some/path --python {handler._folder}")
    assert result is True
