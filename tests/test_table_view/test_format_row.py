from uv_audit.table_view import _format_row


def test_format_row_pads_to_widths():
    # act
    result = _format_row(["a", "bb"], [3, 4])

    # assert
    # "a" padded to 3, "bb" padded to 4, joined with two spaces
    assert result == "a    bb  "
