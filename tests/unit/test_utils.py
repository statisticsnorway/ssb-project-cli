"""Tests utils functions."""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import tomli_w  # type: ignore[import-not-found]

from ssb_project_cli.ssb_project.util import execute_command
from ssb_project_cli.ssb_project.util import get_project_name_and_root_path
from ssb_project_cli.ssb_project.util import set_debug_logging


UTILS = "ssb_project_cli.ssb_project.util"


@patch(f"{UTILS}.create_error_log")
@patch(f"{UTILS}.subprocess.run")
def test_execute_command(mock_run: Mock, mock_create_log: Mock) -> None:
    """Tests whether subprocess was ran at least once and wheter error log was created if failed."""
    mock_run.side_effect = (
        Mock(
            returncode=1,
        ),
    )

    with pytest.raises(SystemExit):
        execute_command("cmd test", "cmd-test", "Success", "Failed", None)

    assert mock_run.call_count == 1

    assert mock_create_log.call_count == 1


@patch(f"{UTILS}.print")
@patch(f"{UTILS}.subprocess.run")
def test_execute_command_success(mock_run: Mock, mock_print: Mock) -> None:
    """Tests whether subprocess was ran at least once and wheter error log was created if failed."""
    mock_run.side_effect = (
        Mock(
            returncode=0,
        ),
    )

    execute_command("cmd test", "cmd-test", "Success", "Failed", None)

    assert mock_run.call_count == 1
    mock_print.assert_called_with("Success")


def test_set_debug_logging_folders_created() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        error_logs_path = Path(f"{tempdir}/ssb-project-cli/.error_logs/")
        set_debug_logging(home_path=Path(tempdir))
        assert error_logs_path.is_dir()


def test_get_project_name_cruft_json(tmp_path: Path) -> None:
    name = "my-project-name"
    content = {"context": {"cookiecutter": {"project_name": name}}}
    with (tmp_path / ".cruft.json").open("w") as f:
        f.write(json.dumps(content))
    assert get_project_name_and_root_path(tmp_path) == (name, tmp_path)


def test_get_project_name_pyproject_toml(tmp_path: Path) -> None:
    name = "my-project-name"
    content = {"tool": {"poetry": {"name": name}}}
    with (tmp_path / "pyproject.toml").open("w") as f:
        f.write(tomli_w.dumps(content))
    assert get_project_name_and_root_path(tmp_path) == (name, tmp_path)


def test_get_project_name_git_directory(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    assert get_project_name_and_root_path(tmp_path) == (tmp_path.name, tmp_path)


def test_get_project_name_nested_directory(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    origin = (
        tmp_path
        / "deeply"
        / "nested"
        / "directory"
        / "structure"
        / "that"
        / "goes"
        / "some"
        / "levels"
        / "down"
    )
    origin.mkdir(parents=True)
    assert get_project_name_and_root_path(origin) == (tmp_path.name, tmp_path)


def test_get_project_name_non_existing_path(tmp_path: Path) -> None:
    assert get_project_name_and_root_path(tmp_path / "fake") == (None, None)


def test_get_project_name_non_project_dir(tmp_path: Path) -> None:
    assert get_project_name_and_root_path(tmp_path) == (None, None)
