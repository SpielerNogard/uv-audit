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
        f"[link]({v['link']}) |"
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


def render_markdown(aggregated: dict, uv_audit_version: str) -> str:
    """Return the full Markdown body for the aggregated report.

    Emits the clean-state body when ``vulnerable`` is False, otherwise the
    full vulnerability layout with collapsible per-file sections.
    """
    if not aggregated["vulnerable"]:
        return render_clean(aggregated["scanned_files"])

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
        "⚠️ Files with findings: " + ", ".join(files_with),
        "",
    ]
    for entry in aggregated["inputs"]:
        section = _render_file_section(entry)
        if section:
            parts.append(section)
            parts.append("")
    ignored = _render_ignored_section(aggregated)
    if ignored:
        parts.append(ignored)
        parts.append("")

    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts.append(f"_Updated: {ts} · uv-audit {uv_audit_version}_")
    return "\n".join(parts)
