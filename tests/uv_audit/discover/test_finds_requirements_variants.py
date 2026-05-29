"""Tests that discover_files finds requirements.txt and variants like requirements-dev.txt."""

from pathlib import Path

from uv_audit.discover import DEFAULT_INCLUDES, discover_files


def test_discover_finds_requirements_variants(tmp_path: Path):
    """Confirm both bare requirements.txt and requirements-*.txt files are matched as 'requirements'."""
    # arrange
    (tmp_path / "requirements.txt").write_text("")
    (tmp_path / "requirements-dev.txt").write_text("")
    (tmp_path / "requirements-prod.txt").write_text("")

    # act
    result = discover_files(root=tmp_path, includes=DEFAULT_INCLUDES, excludes=[])

    # assert
    paths = [entry["path"] for entry in result]
    assert sorted(paths) == [
        "requirements-dev.txt",
        "requirements-prod.txt",
        "requirements.txt",
    ]
    assert all(entry["kind"] == "requirements" for entry in result)
