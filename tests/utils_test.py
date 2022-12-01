"""Tests utils functions."""
from ssb_project_cli.ssb_project.util import execute_command

import pytest

from unittest.mock import Mock
from unittest.mock import patch


UTILS = "ssb_project_cli.ssb_project.util"

@patch(f"{UTILS}.create_error_log")
@patch(f"{UTILS}.subprocess.run")
def test_execute_command(mock_run: Mock, mock_create_log: Mock) -> None:
    """Tests whether subprocess was ran at least once and wheter error log was created if failed.
    """
    mock_run.side_effect = Mock(
            returncode=1,
        ),

    with pytest.raises(SystemExit):
        execute_command("cmd test", "cmd-test", "Success", "Failed", None)


    assert mock_run.call_count == 1


    assert mock_create_log.call_count == 1



