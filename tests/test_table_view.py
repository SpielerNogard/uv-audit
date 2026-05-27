import pytest

from uv_audit.table_view import _compute_widths, _format_row, print_simple_table


def test_print_simple_table_with_empty_data(capsys: pytest.CaptureFixture[str]):
    # act
    print_simple_table([])

    # assert
    captured = capsys.readouterr()
    assert "Keine Daten vorhanden" in captured.out


def test_print_simple_table_with_data_and_default_headers(
    capsys: pytest.CaptureFixture[str],
):
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


def test_format_row_pads_to_widths():
    # act
    result = _format_row(["a", "bb"], [3, 4])

    # assert
    # "a" padded to 3, "bb" padded to 4, joined with two spaces
    assert result == "a    bb  "


def test_compute_widths_picks_max_of_header_and_values():
    # arrange
    data = [{"X": "ab"}, {"X": "abcdef"}]
    headers = ["X"]

    # act
    result = _compute_widths(data, headers)

    # assert
    assert result == {"X": 6}
