from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.create.create import is_memory_full


CREATE = "ssb_project_cli.ssb_project.create.create"


@patch("os.path.exists")
@patch("psutil.disk_usage")
@patch("psutil.swap_memory")
@patch("psutil.virtual_memory")
def test_is_memory_full(
    mock_virtual_memory: Mock,
    mock_swap_memory: Mock,
    mock_disk_usage: Mock,
    mock_exists: Mock,
) -> None:
    # Test the case where both virtual memory and swap memory are below 95% used
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 100
    mock_swap_memory.return_value.used = 10
    mock_swap_memory.return_value.total = 100
    mock_exists.return_value = True
    mock_disk_usage.return_value.used = 10
    mock_disk_usage.return_value.total = 100
    is_memory_full()

    # Test the case where virtual memory is above 95% used
    mock_virtual_memory.return_value.used = 96
    mock_virtual_memory.return_value.total = 100
    mock_swap_memory.return_value.used = 10
    mock_swap_memory.return_value.total = 100
    mock_exists.return_value = True
    mock_disk_usage.return_value.used = 10
    mock_disk_usage.return_value.total = 100
    with pytest.raises(SystemExit):
        is_memory_full()

    # Test the case where swap memory is above 95% used
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 100
    mock_swap_memory.return_value.used = 96
    mock_swap_memory.return_value.total = 100
    mock_exists.return_value = True
    mock_disk_usage.return_value.used = 10
    mock_disk_usage.return_value.total = 100
    with pytest.raises(SystemExit):
        is_memory_full()

    # Test the case where the /home/jovyan/ directory does not exist
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 100
    mock_swap_memory.return_value.used = 10
    mock_swap_memory.return_value.total = 100
    mock_exists.return_value = False
    mock_disk_usage.return_value.used = 10
    mock_disk_usage.return_value.total = 100
    is_memory_full()

    # Test the case where disk memory is above 95% used
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 100
    mock_swap_memory.return_value.used = 96
    mock_swap_memory.return_value.total = 100
    mock_exists.return_value = True
    mock_disk_usage.return_value.used = 98
    mock_disk_usage.return_value.total = 100
    with pytest.raises(SystemExit):
        is_memory_full()

    # Test the case where total swap memory is 0
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 100
    mock_swap_memory.return_value.used = 96
    mock_swap_memory.return_value.total = 0
    mock_exists.return_value = True
    mock_disk_usage.return_value.used = 98
    mock_disk_usage.return_value.total = 100
    with pytest.raises(SystemExit):
        is_memory_full()

    # Test the case where total virtual memory is 0
    mock_virtual_memory.return_value.used = 10
    mock_virtual_memory.return_value.total = 0
    mock_swap_memory.return_value.used = 96
    mock_swap_memory.return_value.total = 0
    mock_exists.return_value = True
    mock_disk_usage.return_value.used = 98
    mock_disk_usage.return_value.total = 100
    with pytest.raises(SystemExit):
        is_memory_full()
