"""Tests for the clean module."""
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.clean.clean import clean_project
from ssb_project_cli.ssb_project.clean.clean import clean_venv


CLEAN = "ssb_project_cli.ssb_project.clean.clean"


@patch(f"{CLEAN}.clean_venv")
@patch(f"{CLEAN}.questionary.confirm")
@patch(f"{CLEAN}.get_kernels_dict")
@patch(f"{CLEAN}.subprocess.run")
def test_clean(
    mock_run: Mock,
    mock_kernels: Mock,
    mock_confirm: Mock,
    _mock_clean_venv: Mock,
) -> None:
    """Check if the function works correctly and raises the expected errors."""
    project_name = "test-project"
    mock_kernels.return_value = {}

    mock_confirm.ask.return_value = True

    with pytest.raises(SystemExit):
        clean_project(project_name)
    kernels = {project_name: "/kernel/path"}
    mock_kernels.return_value = kernels
    mock_run.return_value = Mock(returncode=1, stderr=b"Some error")
    with pytest.raises(SystemExit):
        clean_project(project_name)

    mock_run.return_value = Mock(
        returncode=0,
        stderr=f"[RemoveKernelSpec] Removed {kernels[project_name]}".encode(),
    )

    clean_project(project_name)

    assert mock_run.call_count == 2



@patch(f"{CLEAN}.Path")
@patch(f"{CLEAN}.subprocess.run")
@patch(f"{CLEAN}.questionary")
def test_clean_venv(
    confirm_mock: Mock, run_mock: Mock, path_mock: Mock
) -> None:
    confirm_mock.return_value = True
    path_mock.is_dir.return_value = True

    with pytest.raises(SystemExit):
        clean_venv()

    assert run_mock.call_count == 1

