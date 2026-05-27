"""File discovery for ``uv-audit --discover``.

Walks a directory tree looking for files that match include-globs and
do not match any exclude entry. Returns a sorted list of {path, kind}
dicts where ``kind`` is ``"pyproject"`` for ``pyproject.toml`` and
``"requirements"`` for any other matching file.
"""

import fnmatch
from pathlib import Path

DEFAULT_INCLUDES = ["**/pyproject.toml", "**/requirements*.txt"]
DEFAULT_EXCLUDES = [
    ".venv",
    "venv",
    ".tox",
    "node_modules",
    ".git",
    "dist",
    "build",
    "site-packages",
]


def _kind(path: Path) -> str:
    return "pyproject" if path.name == "pyproject.toml" else "requirements"


def _has_glob_metachars(s: str) -> bool:
    return any(c in s for c in "*?[")


def _is_excluded(rel_path: str, excludes: list[str]) -> bool:
    parts = rel_path.split("/")
    for entry in excludes:
        if _has_glob_metachars(entry):
            if fnmatch.fnmatch(rel_path, entry):
                return True
        elif entry in parts:
            return True
    return False


def discover_files(root: Path, includes: list[str], excludes: list[str]) -> list[dict]:
    """Return matching files under *root* as ``[{path, kind}, ...]``.

    Paths in the result are POSIX-style and relative to *root*. Results
    are sorted by path for determinism. A file is returned iff at least
    one include pattern matches AND no exclude entry matches.

    Exclude semantics:
    * Entries without ``*``, ``?``, or ``[`` are matched as path
      components — any file whose relative path contains the entry as
      a directory segment is skipped.
    * Entries with glob metacharacters are matched as globs against the
      full relative path via :func:`fnmatch.fnmatch`.
    """
    matched: set[Path] = set()
    for pattern in includes:
        for hit in root.glob(pattern):
            if hit.is_file():
                matched.add(hit)

    results = []
    for hit in sorted(matched):
        rel = hit.relative_to(root).as_posix()
        if _is_excluded(rel, excludes):
            continue
        results.append({"path": rel, "kind": _kind(hit)})
    return results
