"""Tests for the environment module."""
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.build.environment import (
    _local_file_contains_remote_lines,
)
from ssb_project_cli.ssb_project.build.environment import running_onprem
from ssb_project_cli.ssb_project.build.environment import verify_local_config


ENVIRONMENT = "ssb_project_cli.ssb_project.build.environment"


@pytest.mark.parametrize(
    "image_spec,expected_result",
    [
        ("prod-bip/ssb/statistikktjenester/jupyterlab-onprem:0.1.3", True),
        ("rod-bip/ssb/dapla/dapla-jupyterlab:1.3.7", False),
    ],
)
def test_running_onprem(image_spec: str, expected_result: bool) -> None:
    assert running_onprem(image_spec) == expected_result


TEST_FILE_PATH = "tests/unit/build_test/test_files/"


@pytest.mark.parametrize(
    "local_file,remote_file,expected_result",
    [
        ("remote_file.txt", "remote_file.txt", True),
        ("local_file_empty.txt", "remote_file.txt", False),
        ("local_file_extra.txt", "remote_file.txt", True),
        ("local_file_partial.txt", "remote_file.txt", False),
    ],
)
def test_local_contains_remote_lines(
    local_file: str, remote_file: str, expected_result: bool
) -> None:
    assert (
        _local_file_contains_remote_lines(
            f"{TEST_FILE_PATH}{local_file}", f"{TEST_FILE_PATH}{remote_file}"
        )
        is expected_result
    )


@patch(f"{ENVIRONMENT}._local_file_contains_remote_lines")
def test_verify_local_config_call_arguments(
    mock_local_file_contains_remote_lines: Mock,
) -> None:
    # Call the main function
    assert verify_local_config(
        "https://github.com/statisticsnorway/ssb-project-template-stat.git", "1.0.0"
    )

    # Check that the local_file_contains_remote_lines function was called twice
    # once for ".gitattributes" and another time for ".gitignore"
    assert mock_local_file_contains_remote_lines.call_count == 2

    # Check that the function was called with the correct arguments for the first call
    assert (
        mock_local_file_contains_remote_lines.call_args_list[0].args[0]
        == ".gitattributes"
    )
    assert (
        "{{cookiecutter.project_name}}/.gitattributes"
        in mock_local_file_contains_remote_lines.call_args_list[0].args[1]
    )

    # Check that the function was called with the correct arguments for the second call
    assert (
        mock_local_file_contains_remote_lines.call_args_list[1].args[0] == ".gitignore"
    )
    assert (
        "{{cookiecutter.project_name}}/.gitignore"
        in mock_local_file_contains_remote_lines.call_args_list[1].args[1]
    )


@pytest.mark.parametrize(
    "first_return,second_return, expected_result",
    [
        (True, True, True),
        (True, False, False),
        (False, False, False),
        (False, True, False),
    ],
)
@patch(f"{ENVIRONMENT}._local_file_contains_remote_lines")
def test_verify_local_config_return_values(
    mock_local_file_contains_remote_lines: Mock,
    first_return: bool,
    second_return: bool,
    expected_result: bool,
) -> None:
    mock_local_file_contains_remote_lines.side_effect = [first_return, second_return]
    assert (
        verify_local_config(
            "https://github.com/statisticsnorway/ssb-project-template-stat.git", "1.0.0"
        )
        is expected_result
    )
