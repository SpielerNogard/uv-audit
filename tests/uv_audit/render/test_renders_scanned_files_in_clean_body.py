"""Tests that the clean (no-vuln) body also includes the scanned-files section."""

from uv_audit.render import render_markdown


def test_render_clean_body_includes_scanned_files():
    """Confirm the clean path lists every scanned file with the ✅ icon."""
    # arrange
    aggregated = {
        "vulnerable": False,
        "scanned_files": 2,
        "vuln_count": 0,
        "ignored_count": 0,
        "ignored_ids": [],
        "dead_ignores": [],
        "scan_errors": [],
        "inputs": [
            {
                "source": "a.toml",
                "kind": "pyproject",
                "groups": [],
                "extras": [],
                "vulnerabilities": [],
            },
            {
                "source": "b.txt",
                "kind": "requirements",
                "groups": [],
                "extras": [],
                "vulnerabilities": [],
            },
        ],
    }

    # act
    result = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert "✅" in result
    assert "No vulnerabilities found in 2 file(s)" in result
    assert "📋 <strong>Scanned files (2)</strong>" in result
    assert "✅ `a.toml`" in result
    assert "✅ `b.txt`" in result
