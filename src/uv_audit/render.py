"""Render an aggregated uv-audit report as GitHub-flavoured Markdown.

Output is used both as the PR sticky-comment body (with the `<!-- uv-audit-report -->`
marker on line 1) and as the workflow step summary.
"""

from datetime import UTC, datetime

MARKER = "<!-- uv-audit-report -->"


def render_clean(scanned_files: int) -> str:
    """Return the body used when no non-ignored vulnerabilities are present."""
    msg = f"✅ **uv-audit:** No vulnerabilities found in {scanned_files} file(s)."
    return f"{MARKER}\n{msg}"


def _render_file_section(entry: dict) -> str:
    visible = [v for v in entry["vulnerabilities"] if not v["ignored"]]
    if not visible:
        return ""
    rows = "\n".join(
        f"| {v['package']} | {v['version']} | {v['id']} | "
        f"{', '.join(v['fix_versions']) or '—'} | "
        f"{'[link](' + v['link'] + ')' if v.get('link') else '—'} |"
        for v in visible
    )
    return (
        f"<details>\n"
        f"<summary><strong>{entry['source']}</strong> — "
        f"{len(visible)} vulnerabilit"
        f"{'y' if len(visible) == 1 else 'ies'}</summary>\n\n"
        f"| Package | Version | ID | Fix | Link |\n"
        f"|---|---|---|---|---|\n"
        f"{rows}\n\n"
        f"</details>"
    )


def _render_ignored_section(aggregated: dict) -> str:
    rows = [
        f"- `{v['id']}` in `{entry['source']}` ({v['package']} {v['version']})"
        for entry in aggregated["inputs"]
        for v in entry["vulnerabilities"]
        if v["ignored"]
    ]
    if not rows:
        return ""
    return (
        f"<details>\n"
        f"<summary>🔇 <strong>Ignored ({len(rows)})</strong></summary>\n\n"
        + "\n".join(rows)
        + "\n\n</details>"
    )


def _scanned_file_row(entry: dict) -> str:
    if entry.get("error"):
        icon, suffix = "❌", " — scan error"
    else:
        visible = sum(1 for v in entry["vulnerabilities"] if not v["ignored"])
        ignored = sum(1 for v in entry["vulnerabilities"] if v["ignored"])
        if visible:
            icon = "⚠️"
            suffix = f" — {visible} vulnerabilit{'y' if visible == 1 else 'ies'}"
        elif ignored:
            icon = "🔇"
            suffix = f" — {ignored} ignored"
        else:
            icon, suffix = "✅", ""
    return f"- {icon} `{entry['source']}` ({entry['kind']}){suffix}"


def _render_scanned_files_section(aggregated: dict) -> str:
    inputs = aggregated.get("inputs") or []
    if not inputs:
        return ""
    rows = "\n".join(_scanned_file_row(e) for e in inputs)
    n = len(inputs)
    return (
        f"<details>\n"
        f"<summary>📋 <strong>Scanned files ({n})</strong></summary>\n\n"
        + rows
        + "\n\n</details>"
    )


def _render_scan_errors_section(aggregated: dict) -> str:
    errors = aggregated.get("scan_errors", [])
    if not errors:
        return ""
    rows = "\n".join(f"- `{e['source']}`: {e['error']}" for e in errors)
    return (
        f"<details>\n"
        f"<summary>⚠️ <strong>Scan failures ({len(errors)})</strong></summary>\n\n"
        + rows
        + "\n\n</details>"
    )


def render_markdown(aggregated: dict, uv_audit_version: str) -> str:
    """Return the full Markdown body for the aggregated report.

    Emits the clean-state body when ``vulnerable`` is False, otherwise the
    full vulnerability layout with collapsible per-file sections.
    """
    if not aggregated["vulnerable"]:
        inputs = aggregated.get("inputs") or []
        if not inputs:
            return render_clean(aggregated["scanned_files"])
        body = (
            f"{MARKER}\n"
            f"✅ **uv-audit:** No vulnerabilities found in "
            f"{aggregated['scanned_files']} file(s).\n\n"
            f"{_render_scanned_files_section(aggregated)}"
        )
        return body

    files_with = [
        f"`{e['source']}` ({sum(1 for v in e['vulnerabilities'] if not v['ignored'])})"
        for e in aggregated["inputs"]
        if any(not v["ignored"] for v in e["vulnerabilities"])
    ]

    parts = [
        MARKER,
        "## 🔍 uv-audit",
        "",
        f"**Scanned {aggregated['scanned_files']} files** · "
        f"**{aggregated['vuln_count']} vulnerabilities** · "
        f"**{aggregated['ignored_count']} ignored**",
        "",
    ]
    if files_with:
        parts.append("⚠️ Files with findings: " + ", ".join(files_with))
        parts.append("")
    for entry in aggregated["inputs"]:
        section = _render_file_section(entry)
        if section:
            parts.append(section)
            parts.append("")
    ignored = _render_ignored_section(aggregated)
    if ignored:
        parts.append(ignored)
        parts.append("")

    scan_errors = _render_scan_errors_section(aggregated)
    if scan_errors:
        parts.append(scan_errors)
        parts.append("")

    scanned = _render_scanned_files_section(aggregated)
    if scanned:
        parts.append(scanned)
        parts.append("")

    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts.append(f"_Updated: {ts} · uv-audit {uv_audit_version}_")
    return "\n".join(parts)
