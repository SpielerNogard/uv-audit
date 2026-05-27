"""Tests for EnvironmentHandler.delete_venv, covering both folder-present and folder-absent scenarios."""

from pytest_mock import MockerFixture

from uv_audit.environment_handler import EnvironmentHandler


def test_delete_venv_when_folder_exists(mocker: MockerFixture):
    """Verify that delete_venv calls rmtree on the folder and returns True when the folder exists."""
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
    """Verify that delete_venv skips rmtree and still returns True when the folder is absent."""
    # arrange
    handler = EnvironmentHandler()
    mocker.patch("uv_audit.environment_handler.os.path.exists", return_value=False)
    rmtree = mocker.patch("uv_audit.environment_handler.shutil.rmtree")

    # act
    result = handler.delete_venv()

    # assert
    assert result is True
    rmtree.assert_not_called()
