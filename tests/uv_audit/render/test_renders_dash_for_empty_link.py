"""Tests that an empty link renders as a placeholder dash, not '[link]()'."""

from uv_audit.render import render_markdown


def test_render_uses_dash_for_empty_link():
    """Confirm a vulnerability with an empty link field shows '—' instead of '[link]()'."""
    # arrange
    aggregated = {
        "vulnerable": True,
        "scanned_files": 1,
        "vuln_count": 1,
        "ignored_count": 0,
        "ignored_ids": [],
        "dead_ignores": [],
        "scan_errors": [],
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
                        "fix_versions": ["2"],
                        "link": "",
                        "ignored": False,
                    }
                ],
            }
        ],
    }

    # act
    result = render_markdown(aggregated, uv_audit_version="0.2.0")

    # assert
    assert "[link]()" not in result
    assert "| p | 1 | X | 2 | — |" in result
