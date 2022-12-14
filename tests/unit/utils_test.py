"""Tests utils functions."""
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.util import execute_command


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
