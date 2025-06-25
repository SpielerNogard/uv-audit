def print_simple_table(data, headers=None):
    if not data:
        print("Keine Daten vorhanden")
        return

    if headers is None:
        headers = list(data[0].keys()) if data else []

    col_widths = {}
    for header in headers:
        col_widths[header] = len(str(header))
        for item in data:
            value = item.get(header, "")
            col_widths[header] = max(col_widths[header], len(str(value)))

    header_row = ""
    for i, header in enumerate(headers):
        if i > 0:
            header_row += "  "
        header_row += str(header).ljust(col_widths[header])
    print(header_row)

    separator = ""
    for i, header in enumerate(headers):
        if i > 0:
            separator += "  "
        separator += "-" * col_widths[header]
    print(separator)

    for item in data:
        row = ""
        for i, header in enumerate(headers):
            if i > 0:
                row += "  "
            value = item.get(header, "")
            row += str(value).ljust(col_widths[header])
        print(row)
