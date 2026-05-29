"""Tests that render_markdown includes the marker comment and the headline summary."""

from uv_audit.render import render_markdown


def test_render_includes_marker_and_summary_line():
    """Confirm the rendered output begins with the marker and contains scanned/vuln/ignored counts."""
    # arrange
    aggregated = {
        "vulnerable": True,
        "scanned_files": 4,
        "vuln_count": 3,
        "ignored_count": 1,
        "ignored_ids": ["X"],
        "inputs": [],
        "dead_ignores": [],
    }

    # act
    result = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert result.startswith("<!-- uv-audit-report -->")
    assert "## 🔍 uv-audit" in result
    assert "**Scanned 4 files** · **3 vulnerabilities** · **1 ignored**" in result
