"""Tests that ignored vulnerabilities appear in their own collapsible 'Ignored' section at the end."""

from uv_audit.render import render_markdown


def test_render_emits_ignored_section_for_suppressed_findings():
    """Confirm a vuln with ignored=True lands in the 🔇 Ignored block, not in the file table."""
    # arrange
    aggregated = {
        "vulnerable": True,
        "scanned_files": 1,
        "vuln_count": 0,
        "ignored_count": 1,
        "ignored_ids": ["PYSEC-2026-161"],
        "dead_ignores": [],
        "inputs": [
            {
                "source": "pyproject.toml",
                "kind": "pyproject",
                "groups": [],
                "extras": [],
                "vulnerabilities": [
                    {
                        "package": "cryptography",
                        "version": "41.0.0",
                        "id": "PYSEC-2026-161",
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
    assert "🔇 <strong>Ignored (1)</strong>" in result
    assert "`PYSEC-2026-161` in `pyproject.toml` (cryptography 41.0.0)" in result
