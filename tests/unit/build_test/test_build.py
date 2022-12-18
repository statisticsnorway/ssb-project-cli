"""Tests for the build module."""
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.build.build import build_project


BUILD = "ssb_project_cli.ssb_project.build.build"


@patch(f"{BUILD}.running_onprem")
@patch(f"{BUILD}.poetry_install")
@patch(f"{BUILD}.install_ipykernel")
@patch(f"{BUILD}.poetry_source_includes_source_name")
@patch(f"{BUILD}.poetry_source_add")
@patch(f"{BUILD}.poetry_source_remove")
@pytest.mark.parametrize(
    "running_onprem_return,poetry_source_includes_source_name_return,calls_to_poetry_source_includes_source_name,calls_to_poetry_source_add,calls_to_poetry_source_remove",
    [
        (False, False, 1, 0, 0),
        (True, False, 0, 1, 0),
        (True, True, 0, 1, 0),
        (False, True, 1, 0, 1),
    ],
)
def test_build(
    mock_poetry_source_remove: Mock,
    mock_poetry_source_add: Mock,
    mock_poetry_source_includes_source_name: Mock,
    mock_install_ipykernel: Mock,
    mock_poetry_install: Mock,
    mock_running_onprem: Mock,
    running_onprem_return: bool,
    poetry_source_includes_source_name_return: bool,
    calls_to_poetry_source_includes_source_name: int,
    calls_to_poetry_source_add: int,
    calls_to_poetry_source_remove: int,
    tmp_path: Path,
) -> None:
    """Check that build calls poetry_install, install_ipykernel and poetry_source_includes_source_name."""
    mock_running_onprem.return_value = running_onprem_return
    mock_poetry_source_includes_source_name.return_value = (
        poetry_source_includes_source_name_return
    )
    build_project(str(tmp_path), tmp_path)
    assert mock_poetry_install.call_count == 1
    assert mock_install_ipykernel.call_count == 1
    assert mock_running_onprem.call_count == 1
    assert (
        mock_poetry_source_includes_source_name.call_count
        == calls_to_poetry_source_includes_source_name
    )
    assert mock_poetry_source_add.call_count == calls_to_poetry_source_add
    assert mock_poetry_source_remove.call_count == calls_to_poetry_source_remove
