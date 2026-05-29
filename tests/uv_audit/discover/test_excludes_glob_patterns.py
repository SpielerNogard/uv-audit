"""Tests that exclude entries containing glob metacharacters match against the full relative path."""

from pathlib import Path

from uv_audit.discover import DEFAULT_INCLUDES, discover_files


def test_discover_excludes_glob_pattern_against_relative_path(tmp_path: Path):
    """Confirm a glob like 'tests/**' excludes nested matches while keeping siblings."""
    # arrange
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "fixtures").mkdir()
    (tmp_path / "tests" / "fixtures" / "pyproject.toml").write_text("")
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "pyproject.toml").write_text("")

    # act
    result = discover_files(
        root=tmp_path, includes=DEFAULT_INCLUDES, excludes=["tests/**"]
    )

    # assert
    paths = [entry["path"] for entry in result]
    assert paths == ["src/pkg/pyproject.toml"]
