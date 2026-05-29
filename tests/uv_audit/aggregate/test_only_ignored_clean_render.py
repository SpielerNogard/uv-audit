"""End-to-end test: when every finding is in ignore_vulns the report renders as clean."""

from uv_audit.aggregate import aggregate
from uv_audit.render import render_markdown


def test_all_findings_ignored_yields_clean_render():
    """Verify aggregate→render reports a clean PR when only ignored vulns exist."""
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
                        "id": "PYSEC-ignored",
                        "fix_versions": [],
                        "link": "",
                    }
                ],
            }
        ]
    }

    # act
    aggregated = aggregate(
        per_file=[payload], ignore_vulns=["PYSEC-ignored"], repo_root="/r"
    )
    body = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert aggregated["vulnerable"] is False
    assert "✅" in body
    assert "No vulnerabilities found" in body
    assert "## 🔍 uv-audit" not in body
