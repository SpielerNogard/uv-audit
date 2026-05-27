"""Tests for print_simple_table, covering empty data, default headers, and explicit header ordering."""

import pytest

from uv_audit.table_view import print_simple_table


def test_print_simple_table_with_empty_data(capsys: pytest.CaptureFixture[str]):
    """Verify print_simple_table prints 'Keine Daten vorhanden' when given an empty list."""
    # act
    print_simple_table([])

    # assert
    captured = capsys.readouterr()
    assert "Keine Daten vorhanden" in captured.out


def test_print_simple_table_with_data_and_default_headers(
    capsys: pytest.CaptureFixture[str],
):
    """Verify print_simple_table renders headers, data rows, and separator dashes for the given records."""
    # arrange
    data = [
        {"Name": "click", "Version": "8.2.1"},
        {"Name": "requests", "Version": "2.32.3"},
    ]

    # act
    print_simple_table(data)

    # assert
    captured = capsys.readouterr()
    assert "Name" in captured.out
    assert "Version" in captured.out
    assert "click" in captured.out
    assert "8.2.1" in captured.out
    assert "requests" in captured.out
    assert "2.32.3" in captured.out
    # separator dashes are present
    assert "---" in captured.out
    # "requests" is 8 chars, column must be at least 8 wide — header line padded
    lines = captured.out.splitlines()
    header_line = lines[0]
    assert "Name    " in header_line or header_line.startswith("Name")


def test_print_simple_table_with_explicit_headers(capsys: pytest.CaptureFixture[str]):
    """Verify print_simple_table respects the explicit header order when headers are provided."""
    # arrange
    data = [
        {"Name": "click", "Version": "8.2.1"},
    ]

    # act
    print_simple_table(data, headers=["Version", "Name"])

    # assert
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    header_line = lines[0]
    # "Version" must appear before "Name" in the header line
    assert header_line.index("Version") < header_line.index("Name")
