"""Tests that discover_files locates pyproject.toml inside a nested subdirectory."""

from pathlib import Path

from uv_audit.discover import discover_files


def test_discover_finds_pyproject_in_subdir(tmp_path: Path):
    """Verify a pyproject.toml two directories deep is returned with kind='pyproject'."""
    # arrange
    nested = tmp_path / "services" / "api"
    nested.mkdir(parents=True)
    (nested / "pyproject.toml").write_text("")

    # act
    result = discover_files(
        root=tmp_path,
        includes=["**/pyproject.toml", "**/requirements*.txt"],
        excludes=[],
    )

    # assert
    assert result == [{"path": "services/api/pyproject.toml", "kind": "pyproject"}]
