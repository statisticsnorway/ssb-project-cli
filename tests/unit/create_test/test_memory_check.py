from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.create.create import is_memory_full


CREATE = "ssb_project_cli.ssb_project.create.create"


@patch(f"{CREATE}.psutil.virtual_memory")
def test_is_memory_full(mock_virtual_memory: Mock) -> None:
    # Set up the mock to return a low percentage of used memory
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 100

    # Call the function and check that it does not exit
    is_memory_full()

    # Set up the mock to return a high percentage of used memory
    mock_virtual_memory.return_value.used = 98
    mock_virtual_memory.return_value.total = 100

    # Call the function and check that it does exit
    with pytest.raises(SystemExit):
        is_memory_full()
