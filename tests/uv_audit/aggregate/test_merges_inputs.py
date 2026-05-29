"""Tests that aggregate() merges per-file scan results and computes top-level counters."""

from uv_audit.aggregate import aggregate


def test_aggregate_merges_inputs_and_counts_vulns():
    """Confirm two per-file payloads merge into one report with correct counters."""
    # arrange
    file_a = {
        "vulnerable": True,
        "inputs": [
            {
                "source": "/abs/a/pyproject.toml",
                "kind": "pyproject",
                "groups": [],
                "extras": [],
                "vulnerabilities": [
                    {
                        "package": "requests",
                        "version": "2.20.0",
                        "id": "GHSA-1",
                        "fix_versions": ["2.32.0"],
                        "link": "https://x",
                    }
                ],
            }
        ],
    }
    file_b = {
        "vulnerable": False,
        "inputs": [
            {
                "source": "/abs/b/requirements.txt",
                "kind": "requirements",
                "groups": [],
                "extras": [],
                "vulnerabilities": [],
            }
        ],
    }

    # act
    result = aggregate(per_file=[file_a, file_b], ignore_vulns=[], repo_root="/abs")

    # assert
    assert result["vulnerable"] is True
    assert result["scanned_files"] == 2
    assert result["vuln_count"] == 1
    assert result["ignored_count"] == 0
    assert result["ignored_ids"] == []
    assert len(result["inputs"]) == 2
    assert result["inputs"][0]["source"] == "a/pyproject.toml"  # relativised
    assert result["inputs"][0]["vulnerabilities"][0]["ignored"] is False
