"""Tests for the build module."""
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.build.build import _get_python_executable_path
from ssb_project_cli.ssb_project.build.build import _write_start_script
from ssb_project_cli.ssb_project.build.build import build_project
from ssb_project_cli.ssb_project.build.build import ipykernel_attach_bashrc
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_DEFAULT_REFERENCE
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_REPO_URL


BUILD = "ssb_project_cli.ssb_project.build.build"


@patch(f"{BUILD}.running_onprem")
@patch(f"{BUILD}.poetry_install")
@patch(f"{BUILD}.install_ipykernel")
@patch(f"{BUILD}.ipykernel_attach_bashrc")
@patch(f"{BUILD}.poetry_source_includes_source_name")
@patch(f"{BUILD}.poetry_source_add")
@patch(f"{BUILD}.poetry_source_remove")
@patch("pathlib.Path.is_file")
@patch("typer.confirm")
@patch("kvakk_git_tools.validate_git_config")
@patch("ssb_project_cli.ssb_project.build.environment.verify_local_config")
@pytest.mark.parametrize(
    "running_onprem_return,poetry_source_includes_source_name_return,calls_to_poetry_source_includes_source_name,calls_to_poetry_source_add,calls_to_poetry_source_remove",
    [
        (False, False, 1, 0, 0),
        (True, False, 1, 1, 0),
        (True, True, 1, 1, 1),
        (False, True, 1, 0, 1),
    ],
)
def test_build(
    mock_verify_local_config: Mock,
    mock_kvakk: Mock,
    mock_confirm: Mock,
    mock_file_found: Mock,
    mock_poetry_source_remove: Mock,
    mock_poetry_source_add: Mock,
    mock_poetry_source_includes_source_name: Mock,
    mock_install_ipykernel: Mock,
    mock_ipykernel_attach_bashrc: Mock,
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
    mock_kvakk.return_value = True
    mock_verify_local_config.return_value = True
    mock_running_onprem.return_value = running_onprem_return
    mock_file_found.return_value = True
    mock_confirm.return_value = False
    mock_poetry_source_includes_source_name.return_value = (
        poetry_source_includes_source_name_return
    )
    build_project(
        tmp_path, tmp_path, STAT_TEMPLATE_REPO_URL, STAT_TEMPLATE_DEFAULT_REFERENCE
    )
    assert mock_kvakk.called
    assert mock_verify_local_config
    assert mock_confirm.call_count == 1
    assert mock_file_found.call_count == 1
    assert mock_poetry_install.call_count == 1
    assert mock_install_ipykernel.call_count == 1
    assert mock_ipykernel_attach_bashrc.call_count == 1
    assert mock_running_onprem.call_count == 1
    assert (
        mock_poetry_source_includes_source_name.call_count
        == calls_to_poetry_source_includes_source_name
    )
    assert mock_poetry_source_add.call_count == calls_to_poetry_source_add
    assert mock_poetry_source_remove.call_count == calls_to_poetry_source_remove


@patch(f"{BUILD}.get_kernels_dict")
@patch("builtins.print")
@patch("builtins.exit")
@patch(f"{BUILD}.Path.exists", side_effect=[True, True, True])
@patch("builtins.open", new_callable=mock_open)
@patch(
    f"{BUILD}.json.loads",
    return_value={
        "argv": [
            "some/path/bin/python3",
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
    },
)
@patch(
    f"{BUILD}.json.dumps",
    return_value='{"argv": ["/bin/python3", "-m", "ipykernel_launcher", "-f", "{connection_file}"]}',
)
@patch(f"{BUILD}._get_python_executable_path")
@patch(f"{BUILD}._write_start_script")
@patch(f"{BUILD}.os.chmod", return_value=True)
def test_ipykernel_attach_bashrc_success(
    mock_chmod: Mock,
    mock_write_start_script: Mock,
    mock_get_python_executable_path: Mock,
    mock_json_dumps: Mock,
    mock_json_loads: Mock,
    mock_file_open: Mock,
    mock_path_exist: Mock,
    mock_exit: Mock,
    mock_print: Mock,
    mock_get_kernels_dict: Mock,
) -> None:
    mock_get_kernels_dict.return_value = {"project_name": "/path/to/project/kernel"}
    project_name = "project_name"

    ipykernel_attach_bashrc(project_name)

    assert mock_get_kernels_dict.call_count == 1
    assert mock_print.call_count == 0
    assert mock_exit.call_count == 0
    assert mock_path_exist.call_count == 2
    assert mock_file_open.call_count == 2
    assert mock_json_loads.call_count == 1
    assert mock_json_dumps.call_count == 1
    assert mock_get_python_executable_path.call_count == 1
    assert mock_write_start_script.call_count == 1
    assert mock_chmod.call_count == 1


@patch(
    f"{BUILD}.get_kernels_dict",
    return_value={"existing_project": "/path/which/does/not/exist"},
)
@patch(f"{BUILD}.print")
def test_ipykernel_attach_bashrc_kernel_not_found(
    mock_print: Mock, mock_get_kernels_dict: Mock
) -> None:
    project_name = "nonexisting_project"
    expected_print_message = f":x:\tCould not mount .bashrc, '{project_name}' is not found in 'jupyter kernelspec list'."  # noqa: B907
    expected_exit_code = 1

    with unittest.TestCase().assertRaises(SystemExit) as cm:
        ipykernel_attach_bashrc(project_name)

    assert mock_get_kernels_dict.call_count == 1
    assert mock_print.call_args[0][0] == expected_print_message
    assert cm.exception.code == expected_exit_code


@patch(
    f"{BUILD}.get_kernels_dict",
    return_value={"existing_project": "/path/which/does/not/exist"},
)
@patch(f"{BUILD}.Path.exists", side_effect=[False])
@patch(f"{BUILD}.print")
def test_ipykernel_attach_bashrc_kernel_path_does_not_exist(
    mock_print: Mock, mock_exists: Mock, mock_get_kernels_dict: Mock
) -> None:
    project_name = "existing_project"
    expected_print_message = ":x:\tCould not mount .bashrc, path: '/path/which/does/not/exist' does not exist."
    expected_exit_code = 1

    with unittest.TestCase().assertRaises(SystemExit) as cm:
        ipykernel_attach_bashrc(project_name)

    assert mock_get_kernels_dict.call_count == 1
    assert mock_exists.call_count == 1
    assert mock_print.call_args[0][0] == expected_print_message
    assert cm.exception.code == expected_exit_code


@patch(
    f"{BUILD}.get_kernels_dict",
    return_value={"existing_project": "/path/which/does/not/exist"},
)
@patch(f"{BUILD}.Path.exists", side_effect=[True, False])
@patch(f"{BUILD}.print")
def test_ipykernel_attach_bashrc_kernel_json_file_not_exist(
    mock_print: Mock, mock_exists: Mock, mock_get_kernels_dict: Mock
) -> None:
    project_name = "existing_project"
    expected_print_message = ":x:\tCould not mount .bashrc, file: '/path/which/does/not/exist/kernel.json' does not exist."
    expected_exit_code = 1

    with unittest.TestCase().assertRaises(SystemExit) as cm:
        ipykernel_attach_bashrc(project_name)

    assert mock_get_kernels_dict.call_count == 1
    assert mock_exists.call_count == 2
    assert mock_print.call_args[0][0] == expected_print_message
    assert cm.exception.code == expected_exit_code


@patch(
    f"{BUILD}.get_kernels_dict",
    return_value={"existing_project": "/path/which/does/not/exist"},
)
@patch(f"{BUILD}.Path.exists", side_effect=[True, True])
@patch("builtins.open", new_callable=mock_open)
@patch(
    f"{BUILD}.json.loads",
    return_value={
        "argv": [
            "some/path/bin/python3",
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
    },
)
@patch(f"{BUILD}._get_python_executable_path", return_value=None)
@patch(f"{BUILD}.print")
def test_ipykernel_attach_bashrc_python_executable_path_not_found(
    mock_print: Mock,
    mock_python_executable_path: Mock,
    mock_json_loads: Mock,
    mock_file_open: Mock,
    mock_exists: Mock,
    mock_get_kernels_dict: Mock,
) -> None:
    project_name = "existing_project"
    expected_print_message = ":x:\tCould not mount .bashrc, cannot find python executable path in /path/which/does/not/exist/kernel.json"
    expected_exit_code = 1

    with unittest.TestCase().assertRaises(SystemExit) as cm:
        ipykernel_attach_bashrc(project_name)

    assert mock_get_kernels_dict.call_count == 1
    assert mock_exists.call_count == 2
    assert mock_file_open.call_count == 1
    assert mock_json_loads.call_count == 1
    assert mock_python_executable_path.call_count == 1
    assert mock_print.call_args[0][0] == expected_print_message
    assert cm.exception.code == expected_exit_code


def test_find_python_executable_path() -> None:
    test_data = [
        "some/path/bin/python3",
        "-m",
        "ipykernel_launcher",
        "-f",
        "{connection_file}",
    ]
    expected_result = "some/path/bin/python3"

    assert _get_python_executable_path(test_data) == expected_result


def test_not_find_python_executable_path() -> None:
    test_data_no_python_path = [
        "/no/python/path",
        "-m",
        "ipykernel_launcher",
        "-f",
        "{connection_file}",
    ]
    expected_result = None

    assert _get_python_executable_path(test_data_no_python_path) == expected_result


@patch("builtins.open", new_callable=mock_open)
def test_write_start_script(mock_file_open: Mock) -> None:
    start_script_path = "/some/place/to/put/test_start_script.sh"
    python_executable_path = "/path/to/bin/python3"

    expected_content = [
        "#!/usr/bin/env bash\n",
        "source $HOME/.bashrc\n",
        "exec /path/to/bin/python3 $@",
    ]

    _write_start_script(start_script_path, python_executable_path)

    mock_file_open.assert_called_once_with(start_script_path, "w", encoding="utf-8")
    mock_file_open().writelines.assert_called_once_with(expected_content)
