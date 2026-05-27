"""File discovery for ``uv-audit --discover``.

Walks a directory tree looking for files that match include-globs and
do not match any exclude entry. Returns a sorted list of {path, kind}
dicts where ``kind`` is ``"pyproject"`` for ``pyproject.toml`` and
``"requirements"`` for any other matching file.
"""

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


def discover_files(root: Path, includes: list[str], excludes: list[str]) -> list[dict]:
    """Return matching files under *root* as ``[{path, kind}, ...]``.

    Paths in the result are POSIX-style and relative to *root*. Results
    are sorted by path for determinism.
    """
    matched: set[Path] = set()
    for pattern in includes:
        for hit in root.glob(pattern):
            if hit.is_file():
                matched.add(hit)

    results = []
    for hit in sorted(matched):
        rel = hit.relative_to(root).as_posix()
        results.append({"path": rel, "kind": _kind(hit)})
    return results
