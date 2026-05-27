"""Tests for the --json output flag, verifying machine-readable JSON emission."""

import json
from pathlib import Path

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from uv_audit import app

runner = CliRunner()


def _write_pyproject(path: Path, body: str) -> Path:
    """Write a pyproject.toml under ``path`` and return its full path.

    Parameters
    ----------
    path : Path
        Directory in which to create the file.
    body : str
        TOML content to write.

    Returns
    -------
    Path
        Absolute path to the newly written file.
    """
    p = path / "pyproject.toml"
    p.write_text(body)
    return p


def test_json_output_for_clean_requirements_file(mocker: MockerFixture, tmp_path: Path):
    """Verify --json emits a valid JSON payload with no vulnerabilities for a clean requirements file.

    Parameters
    ----------
    mocker : MockerFixture
        pytest-mock fixture.
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    # arrange
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.32.3\n")
    mocker.patch("uv_audit.handle_file", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(req_file), "--json"])

    # assert
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["vulnerable"] is False
    assert len(payload["inputs"]) == 1
    assert payload["inputs"][0]["kind"] == "requirements"
    assert payload["inputs"][0]["groups"] == []
    assert payload["inputs"][0]["extras"] == []
    assert payload["inputs"][0]["vulnerabilities"] == []


def test_json_output_for_pyproject_with_vulns(mocker: MockerFixture, tmp_path: Path):
    """Verify --json emits a non-zero exit and correct snake_case vuln fields when vulnerabilities exist.

    Parameters
    ----------
    mocker : MockerFixture
        pytest-mock fixture.
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    # arrange
    py_file = _write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=["flask"]\n',
    )
    mocker.patch(
        "uv_audit.handle_pyproject",
        return_value=[
            {
                "Name": "flask",
                "Version": "1.1.2",
                "ID": "GHSA-X",
                "Fix Versions": "2.0.0",
                "Link": "https://x",
            }
        ],
    )

    # act
    result = runner.invoke(app, ["-r", str(py_file), "--all", "--json"])

    # assert
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["vulnerable"] is True
    assert len(payload["inputs"]) == 1
    vuln = payload["inputs"][0]["vulnerabilities"][0]
    assert vuln["package"] == "flask"
    assert vuln["version"] == "1.1.2"
    assert vuln["id"] == "GHSA-X"
    assert vuln["fix_versions"] == ["2.0.0"]
    assert vuln["link"] == "https://x"


def test_json_output_groups_and_extras_reflect_selection(
    mocker: MockerFixture, tmp_path: Path
):
    """Verify --json payload includes the resolved groups and extras from the pyproject selection.

    Parameters
    ----------
    mocker : MockerFixture
        pytest-mock fixture.
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    # arrange
    py_file = _write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n'
        '\n[project.optional-dependencies]\ncli=["click"]\n'
        '\n[dependency-groups]\ndev=["pytest"]\n',
    )
    mocker.patch("uv_audit.handle_pyproject", return_value=[])

    # act
    result = runner.invoke(app, ["-r", str(py_file), "--all", "--json"])

    # assert
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["inputs"][0]["groups"] == ["dev"]
    assert payload["inputs"][0]["extras"] == ["cli"]


def test_json_output_skips_nonexistent_file_with_stderr_error(tmp_path: Path):
    """Verify --json skips a non-existent path, prints error to stderr, and exits 0.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    # act
    result = runner.invoke(app, ["-r", "/no/such/file", "--json"])

    # assert
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["inputs"] == []
    assert payload["vulnerable"] is False
    assert "does not exist" in result.stderr


def test_json_output_unknown_group_exits_with_stderr_error(tmp_path: Path):
    """Verify --json exits non-zero and prints the unknown group error to stderr without JSON output.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    # arrange
    py_file = _write_pyproject(
        tmp_path,
        '[project]\nname="x"\nversion="0.0.0"\ndependencies=[]\n'
        '\n[dependency-groups]\ndev=["pytest"]\n',
    )

    # act
    result = runner.invoke(app, ["-r", str(py_file), "--group", "missing", "--json"])

    # assert
    assert result.exit_code != 0
    assert "missing" in result.stderr
    assert "dev" in result.stderr


def test_json_output_no_rich_markup_in_stderr(tmp_path: Path):
    """Verify that error messages written to stderr in --json mode contain no Rich markup tags.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    # act / assert
    result = runner.invoke(app, ["-r", "/no/such/file", "--json"])

    assert "[red]" not in result.stderr
    assert "[/red]" not in result.stderr
