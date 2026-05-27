"""Tests that each input with vulnerabilities renders inside a collapsible <details> block."""

from uv_audit.render import render_markdown


def test_render_wraps_file_findings_in_details_block():
    """Confirm a per-file section uses <details>/<summary> and contains a Markdown table."""
    # arrange
    aggregated = {
        "vulnerable": True,
        "scanned_files": 1,
        "vuln_count": 1,
        "ignored_count": 0,
        "ignored_ids": [],
        "dead_ignores": [],
        "inputs": [
            {
                "source": "services/api/pyproject.toml",
                "kind": "pyproject",
                "groups": [],
                "extras": [],
                "vulnerabilities": [
                    {
                        "package": "requests",
                        "version": "2.20.0",
                        "id": "GHSA-x",
                        "fix_versions": ["2.32.0"],
                        "link": "https://x",
                        "ignored": False,
                    }
                ],
            }
        ],
    }

    # act
    result = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert "<details>" in result
    assert "<summary><strong>services/api/pyproject.toml</strong>" in result
    assert "| requests | 2.20.0 | GHSA-x | 2.32.0 | [link](https://x) |" in result
