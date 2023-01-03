from unittest.mock import Mock
from unittest.mock import patch

from ssb_project_cli.ssb_project.create.create import is_memory_full


CREATE = "ssb_project_cli.ssb_project.create.create"


@patch(f"{CREATE}.psutil.virtual_memory")
@patch(f"{CREATE}.psutil.swap_memory")
@patch(f"{CREATE}.psutil.disk_usage")
@patch("os.path.exists")
def test_is_memory_full(
    mock_exists: Mock,
    mock_disk_usage: Mock,
    mock_swap_memory: Mock,
    mock_virtual_memory: Mock,
) -> None:
    # Set up the mock to return a low percentage of used virtual memory
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 100

    # Set up the mock to return a low percentage of used swap memory
    mock_swap_memory.return_value.used = 10
    mock_swap_memory.return_value.total = 100

    # Set up the mock to return True for the os.path.exists() function
    mock_exists.return_value = True

    # Set up the mock to return a low percentage of used disk space
    mock_disk_usage.return_value.used = 10
    mock_disk_usage.return_value.total = 100

    # Call the function and check that it does not exit
    is_memory_full()
