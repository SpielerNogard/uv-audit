"""Tests for the handle_lock orchestration function that delegates to uv audit."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from uv_audit.file_handler import handle_lock

RECORD = {
    "Name": "flask",
    "Version": "1.1.2",
    "ID": "GHSA-1",
    "Fix Versions": "2.0.0",
    "Link": "https://x",
    "Aliases": ["PYSEC-2023-62"],
}


def test_handle_lock_delegates_to_uv_audit(mocker: MockerFixture, tmp_path: Path):
    """Verify handle_lock returns the audit_lock records without creating an environment."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    audit = mocker.patch("uv_audit.file_handler.audit_lock", return_value=[RECORD])
    env_cls = mocker.patch("uv_audit.file_handler.EnvironmentHandler")

    # act
    vulns = handle_lock(lock)

    # assert
    audit.assert_called_once_with(lock)
    env_cls.assert_not_called()
    assert vulns == [RECORD]


def test_handle_lock_omits_aliases_from_the_table(
    mocker: MockerFixture, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Verify the printed table keeps the five display columns and never renders the alias list."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    mocker.patch("uv_audit.file_handler.audit_lock", return_value=[RECORD])

    # act
    handle_lock(lock)

    # assert
    captured = capsys.readouterr()
    assert "Aliases" not in captured.out
    assert "PYSEC-2023-62" not in captured.out
    assert "GHSA-1" in captured.out


def test_handle_lock_quiet_suppresses_output(
    mocker: MockerFixture, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Verify that handle_lock produces no output when quiet=True."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    mocker.patch("uv_audit.file_handler.audit_lock", return_value=[RECORD])

    # act
    vulns = handle_lock(lock, quiet=True)

    # assert
    captured = capsys.readouterr()
    assert len(vulns) == 1
    assert captured.out == ""
    assert captured.err == ""


def test_handle_lock_reports_clean_project(
    mocker: MockerFixture, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Verify a clean lockfile prints the no-vulnerabilities message and returns an empty list."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    mocker.patch("uv_audit.file_handler.audit_lock", return_value=[])

    # act
    vulns = handle_lock(lock)

    # assert
    captured = capsys.readouterr()
    assert vulns == []
    assert "No known vulnerabilities found" in captured.out
