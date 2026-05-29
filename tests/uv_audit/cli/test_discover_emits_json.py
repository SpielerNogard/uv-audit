"""Tests that the CLI's --discover --json mode emits the expected JSON envelope on stdout."""

import json
from pathlib import Path

from uv_audit import app

from .conftest import runner


def test_cli_discover_json_emits_envelope_with_files(tmp_path: Path):
    """Verify --discover --json prints a JSON document with a sorted 'files' list."""
    # arrange
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "pyproject.toml").write_text("")
    (tmp_path / "b" / "pkg").mkdir(parents=True)
    (tmp_path / "b" / "pkg" / "requirements.txt").write_text("")

    # act
    result = runner.invoke(app, ["--discover", "--json", str(tmp_path)])

    # assert
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {
        "files": [
            {"path": "a/pyproject.toml", "kind": "pyproject"},
            {"path": "b/pkg/requirements.txt", "kind": "requirements"},
        ]
    }
