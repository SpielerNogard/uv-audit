"""Parsing and dependency-selection logic for ``pyproject.toml`` files.

This module is responsible for reading a ``pyproject.toml``, validating the
requested extras and dependency-groups against what the file declares, and
returning a :class:`PyProjectSelection` that captures everything the rest of
the pipeline needs to install dependencies.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path


class UnknownExtraError(ValueError):
    """Raised when a requested optional-dependency extra is not declared."""


class UnknownGroupError(ValueError):
    """Raised when a requested dependency group is not declared."""


@dataclass
class PyProjectSelection:
    """Resolved set of dependencies to install from a ``pyproject.toml``.

    Attributes
    ----------
    path : Path
        Path to the ``pyproject.toml`` file.
    extras : list[str]
        Optional-dependency extras that will be installed.
    groups : list[str]
        Dependency groups that will be installed.
    has_main_deps : bool
        Whether the file declares ``[project.dependencies]``.
    """

    path: Path
    extras: list[str]
    groups: list[str]
    has_main_deps: bool


def _validate(
    name: str, available: list[str], kind: str, exc_cls: type[Exception]
) -> None:
    """Assert that *name* is present in *available*, raising *exc_cls* if not.

    Parameters
    ----------
    name : str
        The name to look up (e.g. an extra or group name).
    available : list[str]
        All declared names of the given *kind*.
    kind : str
        Human-readable label used in the error message (e.g. ``"extra"``).
    exc_cls : type[Exception]
        Exception class to raise when *name* is not found.

    Raises
    ------
    Exception
        An instance of *exc_cls* describing the unknown name and listing
        all available names.
    """
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
    """Read a ``pyproject.toml`` and return the resolved dependency selection.

    Parses the TOML file, validates every requested extra and group against the
    declared ones, then applies the ``all_extras``/``all_groups`` shortcuts.
    When neither ``groups`` nor ``all_groups`` is specified, the groups listed
    in ``[tool.uv.default-groups]`` are used as the default.

    Parameters
    ----------
    path : Path
        Path to the ``pyproject.toml`` file to parse.
    extras : list[str]
        Optional-dependency extras explicitly requested by the caller.
    groups : list[str]
        Dependency groups explicitly requested by the caller.
    all_extras : bool
        When ``True``, resolve all declared optional-dependency extras.
    all_groups : bool
        When ``True``, resolve all declared dependency groups.

    Returns
    -------
    PyProjectSelection
        Dataclass holding the resolved extras, groups, and a flag indicating
        whether ``[project.dependencies]`` is present.

    Raises
    ------
    UnknownExtraError
        When any name in *extras* is not declared in the file.
    UnknownGroupError
        When any name in *groups* is not declared in the file.
    """
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
