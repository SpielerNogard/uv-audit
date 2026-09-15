"""Tests for audit_lock, covering command construction, record mapping and error handling."""

import json
import subprocess
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from uv_audit.environment_handler import LockAuditError, audit_lock

PAYLOAD = {
    "schema": {"version": "preview"},
    "summary": {"audited_packages": 6, "vulnerabilities": 2},
    "vulnerabilities": [
        {
            "dependency": {"name": "flask", "version": "1.1.2"},
            "id": "GHSA-m2qf-hxjv-5gpq",
            "display_id": "GHSA-m2qf-hxjv-5gpq",
            "aliases": ["CVE-2023-30861", "PYSEC-2023-62"],
            "link": "https://nvd.nist.gov/vuln/detail/CVE-2023-30861",
            "fix_versions": ["2.2.5", "2.3.2"],
        },
        {
            "dependency": {"name": "jinja2", "version": "3.1.2"},
            "id": "GHSA-noid",
            "display_id": "GHSA-noid",
            "aliases": [],
            "fix_versions": [],
        },
    ],
}


def _completed(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args="uv audit", returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_audit_lock_runs_uv_audit_in_the_lock_directory(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify uv audit is invoked frozen, as JSON, with --directory pointing at the lock's project."""
    # arrange
    lock = tmp_path / "svc" / "uv.lock"
    lock.parent.mkdir()
    lock.write_text("")
    run = mocker.patch(
        "uv_audit.environment_handler.subprocess.run",
        return_value=_completed(0, json.dumps({"vulnerabilities": []})),
    )

    # act
    result = audit_lock(lock)

    # assert
    command = run.call_args.args[0]
    assert command.startswith("uv audit ")
    assert "--frozen" in command
    assert "--output-format json" in command
    assert f"--directory {lock.parent}" in command
    assert result == []


def test_audit_lock_maps_vulnerabilities_to_records(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify uv audit findings become vulnerability records with aliases and N/A fallbacks."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    mocker.patch(
        "uv_audit.environment_handler.subprocess.run",
        return_value=_completed(1, json.dumps(PAYLOAD)),
    )

    # act
    result = audit_lock(lock)

    # assert
    assert result == [
        {
            "Name": "flask",
            "Version": "1.1.2",
            "ID": "GHSA-m2qf-hxjv-5gpq",
            "Fix Versions": "2.2.5, 2.3.2",
            "Link": "https://nvd.nist.gov/vuln/detail/CVE-2023-30861",
            "Aliases": ["CVE-2023-30861", "PYSEC-2023-62"],
        },
        {
            "Name": "jinja2",
            "Version": "3.1.2",
            "ID": "GHSA-noid",
            "Fix Versions": "N/A",
            "Link": "N/A",
            "Aliases": [],
        },
    ]


@pytest.mark.parametrize(
    ("completed", "expected_message"),
    [
        pytest.param(
            _completed(2, "", "error: no `uv.lock` found"),
            "error: no `uv.lock` found",
            id="non-audit-exit-code-reports-stderr",
        ),
        pytest.param(
            _completed(2),
            "uv audit exited with 2",
            id="non-audit-exit-code-without-stderr",
        ),
        pytest.param(
            _completed(0, "not json"),
            "unexpected `uv audit` output",
            id="unparsable-output",
        ),
        pytest.param(
            _completed(0, json.dumps({"vulnerabilities": [{"id": "x"}]})),
            "unexpected `uv audit` output",
            id="output-missing-expected-keys",
        ),
    ],
)
def test_audit_lock_raises_lock_audit_error(
    mocker: MockerFixture,
    tmp_path: Path,
    completed: subprocess.CompletedProcess,
    expected_message: str,
):
    """Verify failures and unexpected preview-schema output raise LockAuditError with a readable message."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    mocker.patch("uv_audit.environment_handler.subprocess.run", return_value=completed)

    # act / assert
    with pytest.raises(LockAuditError, match=expected_message):
        audit_lock(lock)


def test_audit_lock_deduplicates_advisories_reported_under_several_ids(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify an advisory uv reports once as GHSA and once as PYSEC yields a single record."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    dependency = {"name": "flask", "version": "1.1.2"}
    payload = {
        "vulnerabilities": [
            {
                "dependency": dependency,
                "display_id": "GHSA-m2qf-hxjv-5gpq",
                "aliases": ["CVE-2023-30861", "PYSEC-2023-62"],
                "fix_versions": ["2.2.5"],
            },
            {
                "dependency": dependency,
                "display_id": "PYSEC-2023-62",
                "aliases": ["CVE-2023-30861", "GHSA-m2qf-hxjv-5gpq"],
                "fix_versions": ["2.2.5"],
            },
            {
                "dependency": dependency,
                "display_id": "GHSA-68rp-wp8r-4726",
                "aliases": ["CVE-2026-27205"],
                "fix_versions": ["3.1.3"],
            },
        ]
    }
    mocker.patch(
        "uv_audit.environment_handler.subprocess.run",
        return_value=_completed(1, json.dumps(payload)),
    )

    # act
    result = audit_lock(lock)

    # assert
    assert [record["ID"] for record in result] == [
        "GHSA-m2qf-hxjv-5gpq",
        "GHSA-68rp-wp8r-4726",
    ]


def test_audit_lock_keeps_the_same_advisory_for_different_packages(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify deduplication is per package, so one advisory affecting two packages stays twice."""
    # arrange
    lock = tmp_path / "uv.lock"
    lock.write_text("")
    payload = {
        "vulnerabilities": [
            {
                "dependency": {"name": "flask", "version": "1.1.2"},
                "display_id": "GHSA-shared",
                "aliases": [],
                "fix_versions": [],
            },
            {
                "dependency": {"name": "werkzeug", "version": "1.0.1"},
                "display_id": "GHSA-shared",
                "aliases": [],
                "fix_versions": [],
            },
        ]
    }
    mocker.patch(
        "uv_audit.environment_handler.subprocess.run",
        return_value=_completed(1, json.dumps(payload)),
    )

    # act
    result = audit_lock(lock)

    # assert
    assert [record["Name"] for record in result] == ["flask", "werkzeug"]
