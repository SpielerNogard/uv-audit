"""Tests that render_markdown includes a collapsible 'Scanned files' section listing every input."""

from uv_audit.render import render_markdown


def _entry(source: str, vulns=None, error=None):
    e = {
        "source": source,
        "kind": "pyproject",
        "groups": [],
        "extras": [],
        "vulnerabilities": vulns or [],
    }
    if error:
        e["error"] = error
    return e


def test_render_includes_scanned_files_with_mixed_status():
    """Verify the section is present in the vulnerable path and uses the right icon per file."""
    # arrange
    aggregated = {
        "vulnerable": True,
        "scanned_files": 4,
        "vuln_count": 1,
        "ignored_count": 1,
        "ignored_ids": ["X"],
        "dead_ignores": [],
        "scan_errors": [{"source": "broken.toml", "error": "boom"}],
        "inputs": [
            _entry("clean.toml"),
            _entry(
                "vuln.toml",
                vulns=[
                    {
                        "package": "p",
                        "version": "1",
                        "id": "Y",
                        "fix_versions": [],
                        "link": "",
                        "ignored": False,
                    }
                ],
            ),
            _entry(
                "ignored.toml",
                vulns=[
                    {
                        "package": "p",
                        "version": "1",
                        "id": "X",
                        "fix_versions": [],
                        "link": "",
                        "ignored": True,
                    }
                ],
            ),
            _entry("broken.toml", error="boom"),
        ],
    }

    # act
    result = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert "📋 <strong>Scanned files (4)</strong>" in result
    assert "✅ `clean.toml`" in result
    assert "⚠️ `vuln.toml`" in result
    assert "1 vulnerabilit" in result
    assert "🔇 `ignored.toml`" in result
    assert "1 ignored" in result
    assert "❌ `broken.toml`" in result
    assert "scan error" in result
