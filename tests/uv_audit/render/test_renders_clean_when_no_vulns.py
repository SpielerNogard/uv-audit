"""Tests that an aggregated report with no vulnerabilities renders the green clean-state body."""

from uv_audit.render import render_markdown


def test_render_clean_body_when_not_vulnerable():
    """Verify the clean body mentions a scan count and contains no <details> sections."""
    # arrange
    aggregated = {
        "vulnerable": False,
        "scanned_files": 3,
        "vuln_count": 0,
        "ignored_count": 0,
        "ignored_ids": [],
        "dead_ignores": [],
        "inputs": [],
    }

    # act
    result = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert "✅" in result
    assert "No vulnerabilities found in 3 file(s)" in result
    assert "<details>" not in result
