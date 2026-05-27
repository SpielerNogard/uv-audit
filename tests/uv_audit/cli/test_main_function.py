"""Tests for the module-level main() entry point that delegates to the Typer app."""

from pytest_mock import MockerFixture

from uv_audit import main


def test_main_function_invokes_app(mocker: MockerFixture):
    """Verify that calling main() delegates to the Typer app callable."""
    # arrange
    mock_app = mocker.patch("uv_audit.app")

    # act
    main()

    # assert
    mock_app.assert_called_once()
