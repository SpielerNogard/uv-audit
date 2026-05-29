"""Tests that ignore_vulns entries not matching any finding surface as 'dead_ignores'."""

from uv_audit.aggregate import aggregate


def test_aggregate_reports_dead_ignores():
    """Verify ignore_vulns IDs without a matching finding land in the dead_ignores list."""
    # arrange
    payload = {
        "inputs": [
            {
                "source": "/r/req.txt",
                "kind": "requirements",
                "groups": [],
                "extras": [],
                "vulnerabilities": [],
            }
        ]
    }

    # act
    result = aggregate(
        per_file=[payload],
        ignore_vulns=["PYSEC-stale-1", "PYSEC-stale-2"],
        repo_root="/r",
    )

    # assert
    assert result["dead_ignores"] == ["PYSEC-stale-1", "PYSEC-stale-2"]
    assert result["ignored_count"] == 0
