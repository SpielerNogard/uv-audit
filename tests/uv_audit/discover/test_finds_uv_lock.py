"""Tests that discover_files finds uv.lock files and labels them with the 'lock' kind."""

from pathlib import Path

from uv_audit.discover import DEFAULT_INCLUDES, discover_files


def test_discover_finds_uv_lock(tmp_path: Path):
    """Confirm a uv.lock next to a pyproject.toml is discovered as its own 'lock' entry."""
    # arrange
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "uv.lock").write_text("")
    (tmp_path / "svc").mkdir()
    (tmp_path / "svc" / "uv.lock").write_text("")

    # act
    result = discover_files(root=tmp_path, includes=DEFAULT_INCLUDES, excludes=[])

    # assert
    assert result == [
        {"path": "pyproject.toml", "kind": "pyproject"},
        {"path": "svc/uv.lock", "kind": "lock"},
        {"path": "uv.lock", "kind": "lock"},
    ]
