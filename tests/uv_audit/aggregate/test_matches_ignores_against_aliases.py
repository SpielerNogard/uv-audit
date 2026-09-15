"""Tests that an ignore entry also matches a vulnerability's aliases, not just its primary ID."""

from uv_audit.aggregate import aggregate


def _payload() -> dict:
    return {
        "inputs": [
            {
                "source": "/r/uv.lock",
                "kind": "lock",
                "groups": [],
                "extras": [],
                "vulnerabilities": [
                    {
                        "package": "flask",
                        "version": "1.1.2",
                        "id": "GHSA-m2qf-hxjv-5gpq",
                        "fix_versions": [],
                        "link": "",
                        "aliases": ["CVE-2023-30861", "PYSEC-2023-62"],
                    }
                ],
            }
        ]
    }


def test_aggregate_ignores_a_vuln_matched_by_alias():
    """Verify a PYSEC ignore suppresses the finding that uv audit reports under its GHSA ID."""
    # arrange
    payload = _payload()

    # act
    result = aggregate(
        per_file=[payload], ignore_vulns=["PYSEC-2023-62"], repo_root="/r"
    )

    # assert
    assert result["vuln_count"] == 0
    assert result["ignored_count"] == 1
    assert result["vulnerable"] is False
    assert result["ignored_ids"] == ["PYSEC-2023-62"]
    assert result["dead_ignores"] == []
    assert result["inputs"][0]["vulnerabilities"][0]["ignored"] is True


def test_aggregate_keeps_unmatched_alias_ignores_alive_as_dead():
    """Verify an ignore that matches neither the ID nor any alias is still reported as dead."""
    # arrange
    payload = _payload()

    # act
    result = aggregate(
        per_file=[payload], ignore_vulns=["PYSEC-9999-1"], repo_root="/r"
    )

    # assert
    assert result["vuln_count"] == 1
    assert result["ignored_count"] == 0
    assert result["dead_ignores"] == ["PYSEC-9999-1"]
