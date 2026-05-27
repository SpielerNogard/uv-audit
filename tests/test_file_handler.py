from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit.file_handler import handle_pyproject
from uv_audit.pyproject_handler import PyProjectSelection


def test_handle_pyproject_runs_full_flow(mocker: MockerFixture, tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='x'\nversion='0.0.0'\ndependencies=[]\n")
    selection = PyProjectSelection(
        path=pyproject,
        extras=[],
        groups=[],
        has_main_deps=True,
    )

    env_cls = mocker.patch("uv_audit.file_handler.EnvironmentHandler")
    env = env_cls.return_value
    env.list_packages.return_value = ["requests==2.32.3"]

    scanner_cls = mocker.patch("uv_audit.file_handler.VulnerabilityScanner")
    scanner_cls.return_value.run_check.return_value = []

    # act
    vulns = handle_pyproject(selection)

    # assert
    env.create_venv.assert_called_once()
    env.install_pyproject.assert_called_once_with(selection)
    env.list_packages.assert_called_once()
    env.delete_venv.assert_called_once()
    assert vulns == []


def test_handle_pyproject_skips_install_when_nothing_selected(
    mocker: MockerFixture, tmp_path: Path
):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='x'\nversion='0.0.0'\n")
    selection = PyProjectSelection(
        path=pyproject,
        extras=[],
        groups=[],
        has_main_deps=False,
    )

    env_cls = mocker.patch("uv_audit.file_handler.EnvironmentHandler")
    env = env_cls.return_value
    env.list_packages.return_value = []

    scanner_cls = mocker.patch("uv_audit.file_handler.VulnerabilityScanner")
    scanner_cls.return_value.run_check.return_value = []

    # act
    vulns = handle_pyproject(selection)

    # assert
    env.install_pyproject.assert_not_called()
    assert vulns == []
