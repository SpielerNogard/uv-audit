"""Merge per-file ``uv-audit --json`` outputs into a single aggregated report.

The aggregated shape adds top-level counters, marks each vulnerability with
an ``ignored`` flag based on a caller-supplied list of vulnerability IDs,
and relativises absolute file paths against a repo-root.
"""

from pathlib import Path


def aggregate(per_file: list[dict], ignore_vulns: list[str], repo_root: str) -> dict:
    """Return the aggregated report dict.

    Parameters
    ----------
    per_file : list[dict]
        Each element is the JSON payload emitted by ``uv-audit --json`` for
        a single file (an envelope with ``vulnerable`` and ``inputs``).
    ignore_vulns : list[str]
        Vulnerability IDs that should be marked ``ignored: true`` and
        excluded from the ``vuln_count`` (but included in ``ignored_count``).
    repo_root : str
        Absolute path used to relativise the ``source`` field on each input.

    Returns
    -------
    dict
        See the design spec for the full schema.
    """
    ignore_set = set(ignore_vulns)
    seen_ignored: set[str] = set()
    all_inputs: list[dict] = []
    scan_errors: list[dict] = []
    vuln_count = 0
    ignored_count = 0
    root = Path(repo_root)

    for payload in per_file:
        for entry in payload.get("inputs", []):
            src_abs = Path(entry["source"])
            try:
                src_rel = src_abs.relative_to(root).as_posix()
            except ValueError:
                src_rel = entry["source"]

            vulns_out = []
            for v in entry.get("vulnerabilities", []):
                ignored = v["id"] in ignore_set
                if ignored:
                    ignored_count += 1
                    seen_ignored.add(v["id"])
                else:
                    vuln_count += 1
                vulns_out.append({**v, "ignored": ignored})

            aggregated_entry: dict = {
                "source": src_rel,
                "kind": entry["kind"],
                "groups": entry.get("groups", []),
                "extras": entry.get("extras", []),
                "vulnerabilities": vulns_out,
            }
            if "error" in entry:
                aggregated_entry["error"] = entry["error"]
                scan_errors.append({"source": src_rel, "error": entry["error"]})
            all_inputs.append(aggregated_entry)

    return {
        "vulnerable": vuln_count > 0,
        "scanned_files": len(all_inputs),
        "vuln_count": vuln_count,
        "ignored_count": ignored_count,
        "ignored_ids": sorted(seen_ignored),
        "inputs": all_inputs,
        "dead_ignores": sorted(ignore_set - seen_ignored),
        "scan_errors": scan_errors,
    }
