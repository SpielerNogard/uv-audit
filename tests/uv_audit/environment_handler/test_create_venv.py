from pytest_mock import MockerFixture

from uv_audit.environment_handler import EnvironmentHandler


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
