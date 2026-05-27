from uv_audit import app

from .conftest import runner


def test_cli_no_inputs_exits_with_error():
    # act
    result = runner.invoke(app, ["--all"])

    # assert
    assert result.exit_code == 1
    assert "No requirements files or project directory provided" in result.output
