from pathlib import Path

import pytest

from uv_audit.pyproject_handler import (
    PyProjectSelection,
    UnknownExtraError,
    UnknownGroupError,
    resolve_selection,
)


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
    assert selection.extras == []
    assert selection.groups == []


def test_resolve_selection_explicit_extra(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[project.optional-dependencies]\n"
        'cli = ["click==8.2.1"]\n'
        'ml = ["numpy==2.0.0"]\n'
    )

    # act
    selection = resolve_selection(
        path=pyproject,
        extras=["cli"],
        groups=[],
        all_extras=False,
        all_groups=False,
    )

    # assert
    assert selection.extras == ["cli"]
    assert selection.groups == []


def test_resolve_selection_explicit_group(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[dependency-groups]\n"
        'dev = ["pytest==8.4.0"]\n'
        'test = ["coverage==7.0.0"]\n'
    )

    # act
    selection = resolve_selection(
        path=pyproject,
        extras=[],
        groups=["dev"],
        all_extras=False,
        all_groups=False,
    )

    # assert
    assert selection.groups == ["dev"]
    assert selection.extras == []


def test_resolve_selection_unknown_extra_raises(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[project.optional-dependencies]\n"
        'cli = ["click==8.2.1"]\n'
    )

    # act / assert
    with pytest.raises(UnknownExtraError) as exc:
        resolve_selection(
            path=pyproject,
            extras=["does-not-exist"],
            groups=[],
            all_extras=False,
            all_groups=False,
        )
    assert "does-not-exist" in str(exc.value)
    assert "cli" in str(exc.value)


def test_resolve_selection_unknown_group_raises(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[dependency-groups]\n"
        'dev = ["pytest==8.4.0"]\n'
    )

    # act / assert
    with pytest.raises(UnknownGroupError) as exc:
        resolve_selection(
            path=pyproject,
            extras=[],
            groups=["nope"],
            all_extras=False,
            all_groups=False,
        )
    assert "nope" in str(exc.value)
    assert "dev" in str(exc.value)


def test_resolve_selection_all_extras(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[project.optional-dependencies]\n"
        'cli = ["click"]\n'
        'ml = ["numpy"]\n'
    )

    # act
    selection = resolve_selection(
        path=pyproject,
        extras=[],
        groups=[],
        all_extras=True,
        all_groups=False,
    )

    # assert
    assert sorted(selection.extras) == ["cli", "ml"]


def test_resolve_selection_all_groups(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[dependency-groups]\n"
        'dev = ["pytest"]\n'
        'test = ["coverage"]\n'
    )

    # act
    selection = resolve_selection(
        path=pyproject,
        extras=[],
        groups=[],
        all_extras=False,
        all_groups=True,
    )

    # assert
    assert sorted(selection.groups) == ["dev", "test"]


def test_resolve_selection_uses_default_groups_when_nothing_explicit(
    tmp_path: Path,
):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[dependency-groups]\n"
        'dev = ["pytest"]\n'
        'test = ["coverage"]\n'
        "\n"
        "[tool.uv]\n"
        'default-groups = ["dev"]\n'
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
    assert selection.groups == ["dev"]


def test_resolve_selection_explicit_group_overrides_default(tmp_path: Path):
    # arrange
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "demo"\n'
        'version = "0.0.0"\n'
        "dependencies = []\n"
        "\n"
        "[dependency-groups]\n"
        'dev = ["pytest"]\n'
        'test = ["coverage"]\n'
        "\n"
        "[tool.uv]\n"
        'default-groups = ["dev"]\n'
    )

    # act
    selection = resolve_selection(
        path=pyproject,
        extras=[],
        groups=["test"],
        all_extras=False,
        all_groups=False,
    )

    # assert
    assert selection.groups == ["test"]
