import tomllib
from dataclasses import dataclass
from pathlib import Path


class UnknownExtraError(ValueError):
    pass


class UnknownGroupError(ValueError):
    pass


@dataclass
class PyProjectSelection:
    path: Path
    extras: list[str]
    groups: list[str]
    has_main_deps: bool


def _validate(name: str, available: list[str], kind: str) -> None:
    if name in available:
        return
    available_str = ", ".join(sorted(available)) or "<none>"
    message = f"Unknown {kind} '{name}'. Available {kind}s: {available_str}"
    if kind == "extra":
        raise UnknownExtraError(message)
    raise UnknownGroupError(message)


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

    available_extras = list(project.get("optional-dependencies", {}).keys())
    available_groups = list(data.get("dependency-groups", {}).keys())

    for extra in extras:
        _validate(extra, available_extras, "extra")
    for group in groups:
        _validate(group, available_groups, "group")

    return PyProjectSelection(
        path=path,
        extras=list(extras),
        groups=list(groups),
        has_main_deps=has_main_deps,
    )
