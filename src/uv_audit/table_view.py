def _compute_widths(data: list[dict], headers: list[str]) -> dict[str, int]:
    widths = {header: len(str(header)) for header in headers}
    for item in data:
        for header in headers:
            widths[header] = max(widths[header], len(str(item.get(header, ""))))
    return widths


def _format_row(values: list[str], widths: list[int]) -> str:
    return "  ".join(
        value.ljust(width) for value, width in zip(values, widths, strict=True)
    )


def print_simple_table(data: list[dict], headers: list[str] | None = None) -> None:
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
