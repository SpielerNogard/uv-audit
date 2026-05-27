"""Tests that the CLI exits with an error when invoked without any input paths."""

from uv_audit import app

from .conftest import runner


def test_cli_no_inputs_exits_with_error():
    """Ensure the CLI exits with code 1 and an explanatory message when no inputs are given."""
    # act
    result = runner.invoke(app, ["--all"])

    # assert
    assert result.exit_code == 1
    assert "No requirements files or project directory provided" in result.output
