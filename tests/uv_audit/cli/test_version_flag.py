"""Tests that --version prints the package version and exits cleanly."""

from uv_audit import __version__, app

from .conftest import runner


def test_cli_version_flag_prints_version():
    """Ensure --version prints the current __version__ string and exits with code 0."""
    # act
    result = runner.invoke(app, ["--version"])

    # assert
    assert result.exit_code == 0
    assert __version__ in result.output
