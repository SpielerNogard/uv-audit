from uv_audit import __version__, app

from .conftest import runner


def test_cli_version_flag_prints_version():
    # act
    result = runner.invoke(app, ["--version"])

    # assert
    assert result.exit_code == 0
    assert __version__ in result.output
