# .github/actions/report/report.py
"""Aggregate per-file scan JSONs, write step summary, emit outputs.

Reads every ``scan.json`` under the artifacts directory passed via
``--artifacts-dir``, calls :func:`uv_audit.aggregate.aggregate` and
:func:`uv_audit.render.render_markdown`, then:

1. writes the rendered Markdown to ``$GITHUB_STEP_SUMMARY``;
2. writes the aggregated JSON to ``aggregated.json`` and the rendered
   Markdown to ``comment.md`` for downstream consumption;
3. emits ``vulnerable``, ``vuln_count``, ``ignored_count``, and
   ``report_json`` as GitHub Action outputs via ``$GITHUB_OUTPUT``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from uv_audit import __version__
from uv_audit.aggregate import aggregate
from uv_audit.render import render_clean, render_markdown


def _load_per_file(artifacts_dir: Path) -> list[dict]:
    payloads: list[dict] = []
    for scan_file in sorted(artifacts_dir.rglob("scan.json")):
        try:
            payloads.append(json.loads(scan_file.read_text()))
        except json.JSONDecodeError as exc:
            print(
                f"::error::Could not parse {scan_file}: {exc}", file=sys.stderr
            )
            payloads.append({
                "vulnerable": False,
                "inputs": [{
                    "source": str(scan_file),
                    "kind": "unknown",
                    "groups": [],
                    "extras": [],
                    "error": f"could not parse scan.json: {exc}",
                }],
            })
    return payloads


def _split_ignores(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _emit_output(key: str, value: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as fh:
        if "\n" in value:
            fh.write(f"{key}<<UVAUDIT_EOF\n{value}\nUVAUDIT_EOF\n")
        else:
            fh.write(f"{key}={value}\n")


def _write_summary(body: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        Path(summary_path).write_text(body + "\n")


def _handle_no_files() -> int:
    body = "## 🔍 uv-audit\n\nNo matching files found."
    Path("comment.md").write_text(f"<!-- uv-audit-report -->\n{body}\n")
    _write_summary(body)
    _emit_output("vulnerable", "false")
    _emit_output("vuln_count", "0")
    _emit_output("ignored_count", "0")
    _emit_output(
        "report_json",
        json.dumps(
            {
                "vulnerable": False,
                "scanned_files": 0,
                "vuln_count": 0,
                "ignored_count": 0,
                "ignored_ids": [],
                "inputs": [],
                "dead_ignores": [],
            }
        ),
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--ignore-vulns", default="")
    args = parser.parse_args()

    per_file = _load_per_file(Path(args.artifacts_dir))
    ignore_vulns = _split_ignores(args.ignore_vulns)

    if not per_file:
        return _handle_no_files()

    aggregated = aggregate(
        per_file=per_file, ignore_vulns=ignore_vulns, repo_root=args.repo_root
    )

    if aggregated["vulnerable"]:
        body = render_markdown(aggregated, uv_audit_version=__version__)
    else:
        body = render_clean(aggregated["scanned_files"])

    Path("aggregated.json").write_text(json.dumps(aggregated, indent=2))
    Path("comment.md").write_text(body + "\n")
    _write_summary(body)

    if aggregated["dead_ignores"]:
        ids = ", ".join(aggregated["dead_ignores"])
        print(
            f"::notice::{len(aggregated['dead_ignores'])} ignore_vulns entries "
            f"no longer match — consider removing: {ids}"
        )

    if aggregated.get("scan_errors"):
        for se in aggregated["scan_errors"]:
            print(f"::warning::Scan failed for {se['source']}: {se['error']}")

    _emit_output("vulnerable", "true" if aggregated["vulnerable"] else "false")
    _emit_output("vuln_count", str(aggregated["vuln_count"]))
    _emit_output("ignored_count", str(aggregated["ignored_count"]))
    _emit_output("report_json", json.dumps(aggregated))
    return 0


if __name__ == "__main__":
    sys.exit(main())
