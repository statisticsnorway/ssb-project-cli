"""Tests for the clean module."""
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.clean.clean import clean_project
from ssb_project_cli.ssb_project.clean.clean import clean_venv
from ssb_project_cli.ssb_project.util import get_kernels_dict


CLEAN = "ssb_project_cli.ssb_project.clean.clean"


@patch(f"{CLEAN}.clean_venv")
@patch(f"{CLEAN}.get_kernels_dict")
def test_clean(
    mock_kernels: Mock,
    mock_clean_venv: Mock,
) -> None:
    """Check if the function works correctly and raises the expected errors."""
    project_name = "test-project"
    mock_kernels.return_value = {}

    with pytest.raises(SystemExit):
        clean_project(project_name)

    assert mock_clean_venv.call_count == 1


@patch(f"{CLEAN}.execute_command")
@patch(f"{CLEAN}.Path.is_dir")
@patch(f"{CLEAN}.questionary")
def test_clean_venv(mock_confirm: Mock, mock_path: Mock, mock_execute: Mock) -> None:
    """Check that execute command runs"""
    mock_confirm.confirm().ask.return_value = True
    mock_path.is_dir.return_value = True

    clean_venv()

    mock_confirm.confirm().ask.return_value = True
    mock_path.is_dir.return_value = False

    clean_venv()

    assert mock_execute.call_count == 2


@patch(f"{CLEAN}.subprocess.run")
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
