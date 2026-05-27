"""Tests that the --all flag causes the CLI to collect all extras and all dependency groups."""

from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app

from .conftest import runner, write_pyproject


def test_cli_all_flag_implies_all_groups_and_all_extras(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify that --all expands the selection to include every extra and every dependency group."""
    # arrange
    pyproject = write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n'
        '\n[project.optional-dependencies]\ncli=["click"]\n'
        '\n[dependency-groups]\ndev=["pytest"]\n',
    )
    captured = {}

    def fake_handle(selection, quiet: bool = False):
        captured["selection"] = selection
        return []

    mocker.patch("uv_audit.handle_pyproject", side_effect=fake_handle)

    # act
    result = runner.invoke(app, ["-r", str(pyproject), "--all"])

    # assert
    assert result.exit_code == 0, result.output
    assert captured["selection"].extras == ["cli"]
    assert captured["selection"].groups == ["dev"]
