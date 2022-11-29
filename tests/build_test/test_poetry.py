"""Tests for the poetry module."""
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.build.environment import NEXUS_SOURCE_NAME
from ssb_project_cli.ssb_project.build.poetry import poetry_source_includes_source_name
from ssb_project_cli.ssb_project.clean.clean import get_kernels_dict


POETRY = "ssb_project_cli.ssb_project.build.poetry"


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


@patch(f"{POETRY}.execute_command")
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
