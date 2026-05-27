"""Tests for the handle_file orchestration function, verifying the full venv-install-scan-delete flow."""

from pytest_mock import MockerFixture

from uv_audit.file_handler import handle_file


def test_handle_file_runs_full_flow_and_returns_vulns(mocker: MockerFixture):
    """Verify that handle_file creates a venv, installs, scans, deletes the venv, and returns vulnerabilities."""
    # arrange
    env_cls = mocker.patch("uv_audit.file_handler.EnvironmentHandler")
    env = env_cls.return_value
    env.list_packages.return_value = ["flask==1.1.2"]

    scanner_cls = mocker.patch("uv_audit.file_handler.VulnerabilityScanner")
    scanner_cls.return_value.run_check.return_value = [
        {
            "package": "flask",
            "version": "1.1.2",
            "vulnerabilities": [{"id": "GHSA-1", "fixed_in": ["2.0.0"], "link": "x"}],
        }
    ]

    # act
    vulns = handle_file(file_path="/req.txt", is_file=True)

    # assert
    env.create_venv.assert_called_once()
    env.install_requirements.assert_called_once_with(
        requirements_file="/req.txt", is_file=True
    )
    env.delete_venv.assert_called_once()
    assert len(vulns) == 1


def test_handle_file_returns_empty_when_no_vulns(mocker: MockerFixture):
    """Verify that handle_file returns an empty list when the scanner finds no vulnerabilities."""
    # arrange
    env_cls = mocker.patch("uv_audit.file_handler.EnvironmentHandler")
    env = env_cls.return_value
    env.list_packages.return_value = ["x==1"]

    scanner_cls = mocker.patch("uv_audit.file_handler.VulnerabilityScanner")
    scanner_cls.return_value.run_check.return_value = [
        {"package": "x", "version": "1", "vulnerabilities": []}
    ]

    # act
    vulns = handle_file(file_path="/req.txt", is_file=True)

    # assert
    assert vulns == []
