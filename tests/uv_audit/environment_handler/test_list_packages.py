"""Tests for EnvironmentHandler.list_packages, verifying parsing of pip list output."""

from pytest_mock import MockerFixture

from uv_audit.environment_handler import EnvironmentHandler


def test_list_packages_returns_empty_list_when_no_output(mocker: MockerFixture):
    """Verify that list_packages returns an empty list when run_command produces no output."""
    # arrange
    handler = EnvironmentHandler()
    mocker.patch.object(handler, "run_command", return_value="")

    # act
    result = handler.list_packages()

    # assert
    assert result == []


def test_list_packages_returns_parsed_packages(mocker: MockerFixture):
    """Verify that list_packages parses pip list output into 'name==version' strings."""
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
