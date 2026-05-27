from pathlib import Path

from uv_audit.pyproject_handler import PyProjectSelection, resolve_selection


def test_resolve_selection_detects_main_deps(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        'dependencies = ["requests==2.32.3"]\n'
    )

    # act
    selection = resolve_selection(
        path=pyproject,
        extras=[],
        groups=[],
        all_extras=False,
        all_groups=False,
    )

    # assert
    assert isinstance(selection, PyProjectSelection)
    assert selection.path == pyproject
    assert selection.has_main_deps is True
    assert selection.extras == []
    assert selection.groups == []


def test_resolve_selection_missing_main_deps(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "demo"\nversion = "0.0.0"\n')

    # act
    selection = resolve_selection(
        path=pyproject,
        extras=[],
        groups=[],
        all_extras=False,
        all_groups=False,
    )

    # assert
    assert selection.has_main_deps is False
