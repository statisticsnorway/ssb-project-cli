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
def test_clean(
    mock_kernels: Mock,
    mock_confirm: Mock,
    mock_clean_venv: Mock,
) -> None:
    """Check if the function works correctly and raises the expected errors."""
    project_name = "test-project"
    mock_kernels.return_value = {}

    mock_confirm.ask.return_value = True

    with pytest.raises(SystemExit):
        clean_project(project_name)

    kernels = {project_name: "/kernel/path"}
    mock_kernels.return_value = kernels
   
    assert mock_clean_venv.call_count == 1



