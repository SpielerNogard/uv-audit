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


def _validate(
    name: str, available: list[str], kind: str, exc_cls: type[Exception]
) -> None:
    if name in available:
        return
    available_str = ", ".join(sorted(available)) or "<none>"
    raise exc_cls(f"Unknown {kind} '{name}'. Available {kind}s: {available_str}")


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
    default_groups = list(data.get("tool", {}).get("uv", {}).get("default-groups", []))

    for extra in extras:
        _validate(extra, available_extras, "extra", UnknownExtraError)
    for group in groups:
        _validate(group, available_groups, "group", UnknownGroupError)

    resolved_extras = list(available_extras) if all_extras else list(extras)

    if all_groups:
        resolved_groups = list(available_groups)
    elif groups:
        resolved_groups = list(groups)
    else:
        resolved_groups = default_groups

    return PyProjectSelection(
        path=path,
        extras=resolved_extras,
        groups=resolved_groups,
        has_main_deps=has_main_deps,
    )
