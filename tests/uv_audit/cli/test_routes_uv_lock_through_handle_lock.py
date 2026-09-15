"""Tests that a uv.lock path is routed to handle_lock and reported under the 'lock' kind."""

import json
from pathlib import Path

from pytest_mock import MockerFixture

from uv_audit import app
from uv_audit.environment_handler import LockAuditError

from .conftest import runner

RECORD = {
    "Name": "flask",
    "Version": "1.1.2",
    "ID": "GHSA-1",
    "Fix Versions": "2.0.0",
    "Link": "https://x",
    "Aliases": ["PYSEC-2023-62"],
}


def test_cli_routes_uv_lock_through_handle_lock(mocker: MockerFixture, tmp_path: Path):
    """Ensure a uv.lock file is dispatched to handle_lock and not to the other handlers."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    handle_lock_fn = mocker.patch("uv_audit.handle_lock", return_value=[])
    handle_py = mocker.patch("uv_audit.handle_pyproject", return_value=[])
    handle_file_fn = mocker.patch("uv_audit.handle_file", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(lock)])

    # assert
    assert result.exit_code == 0, result.output
    handle_lock_fn.assert_called_once()
    handle_py.assert_not_called()
    handle_file_fn.assert_not_called()


def test_cli_json_output_for_uv_lock_includes_aliases(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify the --json payload labels the input as 'lock' and carries the advisory aliases."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    mocker.patch("uv_audit.handle_lock", return_value=[RECORD])

    # act
    result = runner.invoke(app, ["-r", str(lock), "--json"])

    # assert
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    entry = payload["inputs"][0]
    assert entry["kind"] == "lock"
    assert entry["groups"] == []
    assert entry["extras"] == []
    assert entry["vulnerabilities"][0]["id"] == "GHSA-1"
    assert entry["vulnerabilities"][0]["aliases"] == ["PYSEC-2023-62"]


def test_cli_reports_lock_audit_error_and_continues(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify a failing uv audit prints its message and still scans the remaining inputs."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.32.3\n")
    mocker.patch(
        "uv_audit.handle_lock",
        side_effect=LockAuditError("error: no `uv.lock` found"),
    )
    handle_file_fn = mocker.patch("uv_audit.handle_file", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(lock), "-r", str(req)])

    # assert
    assert result.exit_code == 0, result.output
    assert "no `uv.lock` found" in result.output
    handle_file_fn.assert_called_once()


def test_cli_warns_that_selection_flags_do_not_apply_to_uv_lock(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify --group alongside a uv.lock warns that the flag is ignored for that input."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    mocker.patch("uv_audit.handle_lock", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(lock), "--group", "dev"])

    # assert
    assert result.exit_code == 0, result.output
    assert "ignored" in result.output.lower()
    assert "uv.lock" in result.output
