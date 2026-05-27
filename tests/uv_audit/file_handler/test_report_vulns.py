import pytest

from uv_audit.file_handler import _report_vulns


def test_report_vulns_prints_summary_when_vulns_found(
    capsys: pytest.CaptureFixture[str],
):
    # arrange
    results = [
        {
            "package": "flask",
            "version": "1.1.2",
            "vulnerabilities": [
                {
                    "id": "GHSA-XYZ",
                    "fixed_in": ["2.0.0"],
                    "link": "https://example.com",
                }
            ],
        }
    ]

    # act
    vulns = _report_vulns(results)

    # assert
    captured = capsys.readouterr()
    assert len(vulns) == 1
    assert vulns[0]["Name"] == "flask"
    assert "Found 1 known vulnerabilities" in captured.out
    assert "flask" in captured.out
    assert "GHSA-XYZ" in captured.out


def test_report_vulns_prints_no_vulnerabilities_when_empty(
    capsys: pytest.CaptureFixture[str],
):
    # act
    vulns = _report_vulns([])

    # assert
    captured = capsys.readouterr()
    assert vulns == []
    assert "No known vulnerabilities found" in captured.out
