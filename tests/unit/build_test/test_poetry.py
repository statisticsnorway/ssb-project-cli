"""Tests for the poetry module."""
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, call, mock_open, patch

import pytest
from ssb_project_cli.ssb_project.build.environment import NEXUS_SOURCE_NAME
from ssb_project_cli.ssb_project.poetry import (
    check_and_fix_onprem_source,
    poetry_install,
    poetry_source_add,
    poetry_source_includes_source_name,
    poetry_source_remove,
    poetry_update_lockfile_dependencies,
    should_update_lock_file,
    update_lock,
)

POETRY = "ssb_project_cli.ssb_project.build.poetry"
CLEAN = "ssb_project_cli.ssb_project.clean.clean"


@patch(f"{POETRY}.execute_command")
def test_poetry_install(mock_run: Mock) -> None:
    project_dir = Path(__file__).parent  # Just some dummy dir, not used
    poetry_install(project_dir)
    assert mock_run.call_count == 1
    assert mock_run.call_args[0][0] == ["poetry", "install"]


@patch(f"{POETRY}.execute_command")
def test_poetry_update_lockfile_dependencies(mock_run: Mock) -> None:
    project_dir = Path(__file__).parent  # Just some dummy dir, not used
    poetry_update_lockfile_dependencies(project_dir)
    assert mock_run.call_count == 1
    assert mock_run.call_args[0][0] == ["poetry", "update", "--lock"]


@patch(f"{POETRY}.execute_command")
def test_poetry_source_includes_source_name(mock_run: Mock) -> None:
    mock_run.side_effect = [
        Mock(
            returncode=0,
            stdout=b" name\t: nexus\n url\t: http://example.com\n default\t: yes\n secondary\t: no",
        ),
        Mock(returncode=0, stdout=b"No sources configured for this project."),
        Mock(returncode=1, stderr=b"Some error"),
    ]
    assert poetry_source_includes_source_name(Path("."), source_name=NEXUS_SOURCE_NAME)
    assert not poetry_source_includes_source_name(
        Path("."), source_name=NEXUS_SOURCE_NAME
    )


@pytest.mark.parametrize(
    "isfile,data,expected",
    [
        (
            True,
            """
                    [package.source]
                    type = "legacy"
                    url = "http://pl-nexuspro-p.ssb.no:8081/repository/pypi-proxy/simple"
                    reference = "nexus"
                    [[package]]""",
            False,
        ),
        (
            True,
            """
                    [package.source]
                    type = "legacy"
                    url = "No url"
                    reference = "nexus"
                    [[package]]""",
            True,
        ),
        (
            False,
            """""",
            False,
        ),
    ],
)
def test_should_update_lock_file(isfile: bool, data: str, expected: bool) -> None:
    """Checks if nexus_source_is_set_in_lock returns appropriate truth values."""
    with patch(f"{POETRY}.os.path.isfile", return_value=isfile):
        with patch(f"{POETRY}.open", mock_open(read_data=data)):
            assert expected == should_update_lock_file(
                "http://pl-nexuspro-p.ssb.no:8081/repository/pypi-proxy/simple",
                Path(),
            )


@patch(f"{POETRY}.execute_command")
def test_update_lock_execute_command_call_args(mock_run: Mock) -> None:
    update_lock(Path("fake_path"))
    assert (
        call(
            ["poetry", "lock", "--no-update"],
            "update_lock",
            "Poetry successfully refreshed lock file!",
            "Poetry failed to refresh lock file.",
            cwd=Path("fake_path"),
        )
        in mock_run.call_args_list
    )


def test_poetry_source_remove() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        project_file_path = Path(temp_dir)

        shutil.copyfile(
            "tests/unit/build_test/test_files/test_nexus_source_update_pyproject.toml",
            project_file_path / Path("pyproject.toml"),
        )
        # Confirm that a source exists
        assert poetry_source_includes_source_name(project_file_path) is True
        # Remove the source
        poetry_source_remove(cwd=project_file_path, lock_update=False)
        # Confirm that the source is removed
        assert poetry_source_includes_source_name(project_file_path) is False


def test_poetry_source_add() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        project_file_path = Path(temp_dir)
        fake_pypi_url = "https://fake-pypi.org/simple"

        shutil.copyfile(
            "tests/unit/build_test/test_files/test_nexus_source_add_pyproject.toml",
            project_file_path / Path("pyproject.toml"),
        )

        # Confirm that the no source is set
        assert poetry_source_includes_source_name(project_file_path) is False
        # Add source to pyproject.toml
        poetry_source_add(fake_pypi_url, project_file_path, "fake_pypi")
        # Confirm that the source is set in pyproject.toml
        assert (
            poetry_source_includes_source_name(project_file_path, "fake_pypi") is True
        )

        # Confirm that fake_pypi_url is set in the lockfile
        # should_update_lock_file returns False if the source_url
        # is set in the project lockfile
        assert should_update_lock_file(fake_pypi_url, project_file_path) is False


@patch(f"{POETRY}.running_onprem")
@patch(f"{POETRY}.poetry_source_includes_source_name")
@patch(f"{POETRY}.poetry_source_add")
@patch(f"{POETRY}.poetry_source_remove")
@pytest.mark.parametrize(
    "running_onprem_return,poetry_source_includes_source_name_return,calls_to_poetry_source_includes_source_name,calls_to_poetry_source_add,calls_to_poetry_source_remove",
    [
        (False, False, 1, 0, 0),
        (True, False, 1, 1, 0),
        (True, True, 1, 1, 1),
        (False, True, 1, 0, 1),
    ],
)
def test_check_and_fix_onprem_source(
    mock_poetry_source_remove: Mock,
    mock_poetry_source_add: Mock,
    mock_poetry_source_includes_source_name: Mock,
    mock_running_onprem: Mock,
    running_onprem_return: bool,
    poetry_source_includes_source_name_return: bool,
    calls_to_poetry_source_includes_source_name: int,
    calls_to_poetry_source_add: int,
    calls_to_poetry_source_remove: int,
    tmp_path: Path,
) -> None:
    mock_running_onprem.return_value = running_onprem_return
    mock_poetry_source_includes_source_name.return_value = (
        poetry_source_includes_source_name_return
    )

    check_and_fix_onprem_source(tmp_path)

    assert mock_running_onprem.call_count == 1
    assert (
        mock_poetry_source_includes_source_name.call_count
        == calls_to_poetry_source_includes_source_name
    )
    assert mock_poetry_source_add.call_count == calls_to_poetry_source_add
    assert mock_poetry_source_remove.call_count == calls_to_poetry_source_remove
