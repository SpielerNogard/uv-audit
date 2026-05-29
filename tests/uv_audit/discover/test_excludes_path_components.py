"""Tests that exclude entries without glob metacharacters skip matching directory components."""

from pathlib import Path

from uv_audit.discover import DEFAULT_EXCLUDES, DEFAULT_INCLUDES, discover_files


def test_discover_excludes_dotvenv_anywhere_in_path(tmp_path: Path):
    """Verify a '.venv' entry skips both top-level .venv/ and nested pkg/.venv/ trees."""
    # arrange
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "pyproject.toml").write_text("")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / ".venv").mkdir()
    (tmp_path / "pkg" / ".venv" / "requirements.txt").write_text("")
    (tmp_path / "pkg" / "pyproject.toml").write_text("")

    # act
    result = discover_files(
        root=tmp_path, includes=DEFAULT_INCLUDES, excludes=DEFAULT_EXCLUDES
    )

    # assert
    paths = [entry["path"] for entry in result]
    assert paths == ["pkg/pyproject.toml"]
