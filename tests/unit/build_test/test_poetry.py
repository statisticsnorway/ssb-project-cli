"""Tests for the poetry module."""
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.build.environment import NEXUS_SOURCE_NAME
from ssb_project_cli.ssb_project.build.poetry import poetry_source_includes_source_name
from ssb_project_cli.ssb_project.build.poetry import should_update_lock_file
from ssb_project_cli.ssb_project.clean.clean import get_kernels_dict


POETRY = "ssb_project_cli.ssb_project.build.poetry"
CLEAN = "ssb_project_cli.ssb_project.clean.clean"


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
