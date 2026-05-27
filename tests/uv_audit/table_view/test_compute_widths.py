"""Tests for the _compute_widths helper that calculates column widths for the table renderer."""

from uv_audit.table_view import _compute_widths


def test_compute_widths_picks_max_of_header_and_values():
    """Verify _compute_widths returns the maximum of the header length and all value lengths per column."""
    # arrange
    data = [{"X": "ab"}, {"X": "abcdef"}]
    headers = ["X"]

    # act
    result = _compute_widths(data, headers)

    # assert
    assert result == {"X": 6}
