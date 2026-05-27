import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PyProjectSelection:
    path: Path
    extras: list[str]
    groups: list[str]
    has_main_deps: bool


def resolve_selection(
    path: Path,
    extras: list[str],
    groups: list[str],
    all_extras: bool,
    all_groups: bool,
) -> PyProjectSelection:
    with path.open("rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    has_main_deps = "dependencies" in project

    return PyProjectSelection(
        path=path,
        extras=[],
        groups=[],
        has_main_deps=has_main_deps,
    )
