"""Tests that vulnerabilities whose IDs appear in ignore_vulns are marked and counted separately."""

from uv_audit.aggregate import aggregate


def test_aggregate_marks_matching_ids_as_ignored():
    """Verify a vuln whose ID is in ignore_vulns has ignored=True and is excluded from vuln_count."""
    # arrange
    payload = {
        "inputs": [
            {
                "source": "/r/pyproject.toml",
                "kind": "pyproject",
                "groups": [],
                "extras": [],
                "vulnerabilities": [
                    {
                        "package": "p",
                        "version": "1",
                        "id": "PYSEC-2026-161",
                        "fix_versions": [],
                        "link": "",
                    },
                    {
                        "package": "q",
                        "version": "2",
                        "id": "GHSA-other",
                        "fix_versions": [],
                        "link": "",
                    },
                ],
            }
        ]
    }

    # act
    result = aggregate(
        per_file=[payload], ignore_vulns=["PYSEC-2026-161"], repo_root="/r"
    )

    # assert
    assert result["vuln_count"] == 1
    assert result["ignored_count"] == 1
    assert result["vulnerable"] is True
    assert result["ignored_ids"] == ["PYSEC-2026-161"]
    vulns = result["inputs"][0]["vulnerabilities"]
    assert vulns[0]["ignored"] is True
    assert vulns[1]["ignored"] is False
