"""Tests that the 'Files with findings:' line is omitted when no files have non-ignored vulnerabilities."""

from uv_audit.render import render_markdown


def test_render_omits_empty_findings_line_when_all_ignored():
    """Confirm the ⚠️ Files with findings line is not emitted when there are no non-ignored vulns."""
    # arrange
    aggregated = {
        "vulnerable": True,
        "scanned_files": 1,
        "vuln_count": 0,
        "ignored_count": 1,
        "ignored_ids": ["X"],
        "dead_ignores": [],
        "inputs": [
            {
                "source": "p.toml",
                "kind": "pyproject",
                "groups": [],
                "extras": [],
                "vulnerabilities": [
                    {
                        "package": "p",
                        "version": "1",
                        "id": "X",
                        "fix_versions": [],
                        "link": "",
                        "ignored": True,
                    }
                ],
            }
        ],
    }

    # act
    result = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert "Files with findings:" not in result
