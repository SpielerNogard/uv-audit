"""Tests for the handle_pyproject orchestration function, including skip-compile and extras-only cases."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from uv_audit.file_handler import handle_pyproject
from uv_audit.pyproject_handler import PyProjectSelection


def test_handle_pyproject_runs_full_flow(mocker: MockerFixture, tmp_path: Path):
    """Verify handle_pyproject compiles the selection and scans the resolved requirements."""
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
    env.compile_pyproject.return_value = ["requests==2.32.3"]

    scanner_cls = mocker.patch("uv_audit.file_handler.VulnerabilityScanner")
    scanner_cls.return_value.run_check.return_value = []

    # act
    vulns = handle_pyproject(selection)

    # assert
    env.compile_pyproject.assert_called_once_with(selection)
    env.create_venv.assert_not_called()
    env.install_requirements.assert_not_called()
    env.list_packages.assert_not_called()
    env.delete_venv.assert_not_called()
    scanner_cls.return_value.run_check.assert_called_once_with(
        requirements=["requests==2.32.3"]
    )
    assert vulns == []


def test_handle_pyproject_skips_compile_when_nothing_selected(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify that handle_pyproject does not invoke compile when has_main_deps is False and no extras or groups are selected."""
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

    # act
    vulns = handle_pyproject(selection)

    # assert
    env.compile_pyproject.assert_not_called()
    assert vulns == []


def test_handle_pyproject_compiles_when_extras_only(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify that handle_pyproject calls compile_pyproject when extras are selected even without main deps."""
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='x'\nversion='0.0.0'\n")
    selection = PyProjectSelection(
        path=pyproject,
        extras=["cli"],
        groups=[],
        has_main_deps=False,
    )

    env_cls = mocker.patch("uv_audit.file_handler.EnvironmentHandler")
    env = env_cls.return_value
    env.compile_pyproject.return_value = []

    # act
    handle_pyproject(selection)

    # assert
    env.compile_pyproject.assert_called_once_with(selection)


def test_handle_pyproject_quiet_suppresses_output(
    mocker: MockerFixture, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Verify that handle_pyproject produces no output when quiet=True."""
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
    env.compile_pyproject.return_value = ["flask==1.1.2"]

    scanner_cls = mocker.patch("uv_audit.file_handler.VulnerabilityScanner")
    scanner_cls.return_value.run_check.return_value = [
        {
            "package": "flask",
            "version": "1.1.2",
            "vulnerabilities": [{"id": "GHSA-1", "fixed_in": ["2.0.0"], "link": "x"}],
        }
    ]

    # act
    vulns = handle_pyproject(selection, quiet=True)

    # assert
    captured = capsys.readouterr()
    assert len(vulns) == 1
    assert captured.out == ""
    assert captured.err == ""
