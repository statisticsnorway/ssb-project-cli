"""Tests for the poetry module."""
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.build.environment import NEXUS_SOURCE_NAME
from ssb_project_cli.ssb_project.build.poetry import install_ipykernel
from ssb_project_cli.ssb_project.build.poetry import poetry_install
from ssb_project_cli.ssb_project.build.poetry import poetry_source_add
from ssb_project_cli.ssb_project.build.poetry import poetry_source_includes_source_name
from ssb_project_cli.ssb_project.build.poetry import poetry_source_remove
from ssb_project_cli.ssb_project.clean.clean import get_kernels_dict


POETRY = "ssb_project_cli.ssb_project.build.poetry"


@patch(f"{POETRY}.create_error_log")
@patch(f"{POETRY}.subprocess.run")
def test_install_ipykernel(mock_run: Mock, mock_log: Mock, tmp_path: Path) -> None:
    """Check that install_ipykernel runs correct command and fails as expected."""
    name = "testproject"
    mock_run.return_value = Mock(returncode=1, stderr=b"some error")
    with pytest.raises(SystemExit):
        install_ipykernel(tmp_path, name)
    assert mock_log.call_count == 1
    assert (
        " ".join(mock_run.call_args[0][0])
        == f"poetry run python3 -m ipykernel install --user --name {name}"
    )
    mock_run.return_value = Mock(returncode=0, stdout=b"No error")

    install_ipykernel(tmp_path, name)
    assert mock_run.call_count == 2
    assert mock_log.call_count == 1


@patch(f"{POETRY}.create_error_log")
@patch(f"{POETRY}.subprocess.run")
def test_poetry_install(mock_run: Mock, mock_log: Mock, tmp_path: Path) -> None:
    """Check if function runs and fails correctly."""
    mock_run.return_value = Mock(returncode=1, stderr=b"some error")
    with pytest.raises(SystemExit):
        poetry_install(tmp_path)
    assert mock_log.call_count == 1
    assert mock_run.call_args[0][0] == "poetry install".split()
    mock_run.return_value = Mock(returncode=0)
    poetry_install(tmp_path)
    assert mock_run.call_count == 2
    assert mock_log.call_count == 1


@patch(f"{POETRY}.subprocess.run")
def test_poetry_source_add(mock_run: Mock) -> None:
    mock_run.side_effect = [
        Mock(
            returncode=0,
            stdout=f"Adding source with name {NEXUS_SOURCE_NAME}.",
        ),
        Mock(returncode=1, stderr=b"Some error"),
    ]
    poetry_source_add("http://example.com", Path("."), source_name=NEXUS_SOURCE_NAME)
    with pytest.raises(ValueError):
        poetry_source_add(
            "http://example.com", Path("."), source_name=NEXUS_SOURCE_NAME
        )


@patch(f"{POETRY}.subprocess.run")
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
    with pytest.raises(ValueError):
        poetry_source_add(
            "http://example.com", Path("."), source_name=NEXUS_SOURCE_NAME
        )


@patch(f"{POETRY}.subprocess.run")
def test_poetry_source_remove(mock_run: Mock) -> None:
    mock_run.side_effect = [
        Mock(
            returncode=0,
            stdout=f"Removing source with name {NEXUS_SOURCE_NAME}.",
        ),
        Mock(returncode=1, stderr=b"Some error"),
    ]
    poetry_source_remove(Path("."), source_name=NEXUS_SOURCE_NAME)
    with pytest.raises(ValueError):
        poetry_source_remove(Path("."), source_name=NEXUS_SOURCE_NAME)


@patch(f"{POETRY}.subprocess.run")
def test_get_kernels_dict(mock_run: Mock) -> None:
    """Checks that get_kernels_dict correctly parses jupyter output."""
    mock_run.side_effect = [
        Mock(
            returncode=0,
            stdout=b"Available kernels:\n  python    /some/path\n  R    /other/path\nthis line is invalid",
        ),
        Mock(returncode=1, stderr=b"Some error"),
    ]
    assert get_kernels_dict() == {"python": "/some/path", "R": "/other/path"}
    with pytest.raises(SystemExit):
        get_kernels_dict()
