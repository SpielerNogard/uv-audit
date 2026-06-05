## 0.3.3 (2026-06-05)

### Fix

- **env**: resolve pyproject deps via `uv pip compile` to skip wheel build (#10)

## 0.3.2 (2026-06-01)

### Fix

- **action**: inline discover and report into root action (#9)

## 0.3.1 (2026-05-29)

### Fix

- **ci**: use BUMP_TOKEN PAT so tag-push triggers publish (#8)

## 0.3.0 (2026-05-29)

### Feat

- **ci**: drop reusable workflow, revert bump infra to default token (#7)
- distribute uv-audit as a GitHub Action with sticky PR comments (#5)

### Fix

- **ci**: repair scan.yml workflow and switch bump to SSH deploy key (#6)

## 0.2.0 (2026-05-27)

### Feat

- **cli**: add --json output flag
- **handlers**: add quiet flag to suppress output
- **cli**: add pyproject auto-detect with --group/--extra/--all-* flags
- **file-handler**: add handle_pyproject flow
- **env**: add install_pyproject for extras and groups
- **pyproject**: support --all-* flags and default-groups fallback
- **pyproject**: validate explicit extras and groups
- **pyproject**: add PyProjectSelection with main-deps detection
- use typer and richt for the cli interface (#1)
- **uv-audit**: uv-audit now exits with an error, when vulns are found
- **uv-audit**: allow to handle projects
- **interface**: streamline interface with pip-audit
- **uv-run**: install the repository now
- **main**: added support for uv run

### Fix

- close [/red] tags, correct commitizen path, raise coverage threshold to 90%
- **env**: shell-quote group arguments and tighten coverage threshold
- **env**: shell-quote install target and tighten install_pyproject tests
- resolve ruff lint issues from expanded ruleset
- fixed script requirements
- **project**: fixed pyproject.toml

### Refactor

- **tests**: mirror src/uv_audit package layout under tests/uv_audit
- **tests**: reorganize into folder-per-module / file-per-function
- **file-handler**: extract _report_vulns helper and tighten tests
- **pyproject**: pass exception class explicitly to _validate
- migrate to src layout and fix pyright types
