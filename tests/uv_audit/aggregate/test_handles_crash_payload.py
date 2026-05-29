"""Tests that aggregate() handles per-file payloads with an 'error' field and no 'vulnerabilities' key."""

from uv_audit.aggregate import aggregate


def test_aggregate_handles_crash_payload_with_error_field():
    """Verify a crash-style input is aggregated without raising and surfaces in scan_errors."""
    # arrange
    payload = {
        "vulnerable": False,
        "inputs": [
            {
                "source": "/r/broken/pyproject.toml",
                "kind": "pyproject",
                "groups": [],
                "extras": [],
                "error": "uv-audit exit 2",
            }
        ],
    }

    # act
    result = aggregate(per_file=[payload], ignore_vulns=[], repo_root="/r")

    # assert
    assert result["scan_errors"] == [
        {"source": "broken/pyproject.toml", "error": "uv-audit exit 2"}
    ]
    assert result["inputs"][0]["error"] == "uv-audit exit 2"
    assert result["inputs"][0]["vulnerabilities"] == []
    assert result["vuln_count"] == 0
