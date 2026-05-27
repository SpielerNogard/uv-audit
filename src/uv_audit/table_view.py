"""Plain-text table renderer for vulnerability output.

Renders a list of dicts as a left-aligned, fixed-width table printed to
stdout.  No external dependencies are required beyond the Python standard
library.
"""


def _compute_widths(data: list[dict], headers: list[str]) -> dict[str, int]:
    """Compute the minimum column width required for each header.

    The width of each column is the maximum of the header label length and the
    longest value that appears in that column across all rows.

    Parameters
    ----------
    data : list[dict]
        Rows of data; each dict maps header names to cell values.
    headers : list[str]
        Column names that determine the order and set of columns to measure.

    Returns
    -------
    dict[str, int]
        Mapping from each header name to its required column width.

    Examples
    --------
    >>> rows = [
    ...     {"Name": "requests", "Version": "2.0"},
    ...     {"Name": "x", "Version": "10.0.1"},
    ... ]
    >>> _compute_widths(rows, ["Name", "Version"])
    {'Name': 8, 'Version': 7}
    """
    widths = {header: len(str(header)) for header in headers}
    for item in data:
        for header in headers:
            widths[header] = max(widths[header], len(str(item.get(header, ""))))
    return widths


def _format_row(values: list[str], widths: list[int]) -> str:
    """Format a single table row with two-space column separators.

    Each value is left-justified to the corresponding width, and columns are
    joined by two spaces.

    Parameters
    ----------
    values : list[str]
        Cell values for this row, one per column.
    widths : list[int]
        Column widths in the same order as *values*.

    Returns
    -------
    str
        A single formatted row string ready to be printed.

    Examples
    --------
    >>> _format_row(["requests", "2.0"], [10, 5])
    'requests    2.0  '
    """
    return "  ".join(
        value.ljust(width) for value, width in zip(values, widths, strict=True)
    )


def print_simple_table(data: list[dict], headers: list[str] | None = None) -> None:
    """Print *data* as a plain-text fixed-width table to stdout.

    Column widths are computed automatically from the data.  When *headers* is
    omitted, the keys of the first row are used as column names in insertion
    order.  A separator row of dashes is printed between the header and the
    data rows.

    Parameters
    ----------
    data : list[dict]
        Rows to display.  Each dict should contain at least the keys listed in
        *headers*.
    headers : list[str] or None, optional
        Column names and their display order.  When ``None`` (default), the
        keys of ``data[0]`` are used.
    """
    if not data:
        print("Keine Daten vorhanden")
        return

    if headers is None:
        headers = list(data[0].keys())

    widths = _compute_widths(data, headers)
    col_widths = [widths[h] for h in headers]

    print(_format_row([str(h) for h in headers], col_widths))
    print(_format_row(["-" * w for w in col_widths], col_widths))
    for item in data:
        print(_format_row([str(item.get(h, "")) for h in headers], col_widths))
