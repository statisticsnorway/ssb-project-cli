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


@patch(f"{BUILD}.check_and_fix_onprem_source")
@patch(f"{BUILD}.poetry_install")
@patch(f"{BUILD}.install_ipykernel")
@patch(f"{BUILD}.ipykernel_attach_bashrc")
@patch("typer.confirm")
@patch("kvakk_git_tools.validate_git_config")
@patch("ssb_project_cli.ssb_project.build.environment.verify_local_config")
@patch(f"{BUILD}.get_project_name_and_root_path")
@pytest.mark.parametrize("no_kernel", [False, True])
def test_build(
    mock_get_project_name_and_root_path: Mock,
    mock_verify_local_config: Mock,
    mock_kvakk: Mock,
    mock_confirm: Mock,
    mock_install_ipykernel: Mock,
    mock_ipykernel_attach_bashrc: Mock,
    mock_poetry_install: Mock,
    mock_check_and_fix_onprem_source: Mock,
    no_kernel: bool,
    tmp_path: Path,
) -> None:
    """Check that build calls poetry_install, install_ipykernel and poetry_source_includes_source_name."""
    mock_kvakk.return_value = True
    mock_verify_local_config.return_value = True
    mock_confirm.return_value = False
    mock_get_project_name_and_root_path.return_value = ("project_name", tmp_path)
    build_project(
        tmp_path,
        tmp_path,
        STAT_TEMPLATE_REPO_URL,
        STAT_TEMPLATE_DEFAULT_REFERENCE,
        True,
        no_kernel,
    )
    assert mock_kvakk.called
    assert mock_verify_local_config
    assert mock_confirm.call_count == 1
    assert mock_poetry_install.call_count == 1
    assert mock_install_ipykernel.call_count == int(not no_kernel)
    assert mock_ipykernel_attach_bashrc.call_count == int(not no_kernel)
    assert mock_check_and_fix_onprem_source.call_count == 1


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
@patch(f"{BUILD}._get_python_executable_path", return_value="/some/path/python3")
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
    mock_get_kernels_dict.return_value = {
        "project_name": {"resource_dir": "/path/to/project/kernel"}
    }
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
    expected_print_message = f":x:\tCould not mount .bashrc, '{project_name}' kernel was not found'."  # noqa: B907
    expected_exit_code = 1

    with unittest.TestCase().assertRaises(SystemExit) as cm:
        ipykernel_attach_bashrc(project_name)

    assert mock_get_kernels_dict.call_count == 1
    assert mock_print.call_args[0][0] == expected_print_message
    assert cm.exception.code == expected_exit_code


@patch(
    f"{BUILD}.get_kernels_dict",
    return_value={"existing_project": {"resource_dir": "/path/which/does/not/exist"}},
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
    return_value={"existing_project": {"resource_dir": "/path/which/does/not/exist"}},
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
    return_value={"existing_project": {"resource_dir": "/path/which/does/not/exist"}},
)
@patch(f"{BUILD}.Path.exists", side_effect=[True, True])
@patch("builtins.open", new_callable=mock_open)
@patch(
    f"{BUILD}.json.loads",
    return_value={
        "argv": [
            "some/path/bin/doesnotexist",
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
    },
)
@patch(f"{BUILD}.print")
def test_ipykernel_attach_bashrc_python_executable_path_not_found(
    mock_print: Mock,
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
    assert mock_print.call_args[0][0] == expected_print_message
    assert cm.exception.code == expected_exit_code


@patch(
    f"{BUILD}.get_kernels_dict",
    return_value={"existing_project": {"resource_dir": "/path/which/does/not/exist"}},
)
@patch(f"{BUILD}.Path.exists", side_effect=[True, True])
@patch("builtins.open", new_callable=mock_open)
@patch(
    f"{BUILD}.json.loads",
    return_value={
        "argv": [
            "some/path/bin/python.sh",
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
    },
)
@patch(f"{BUILD}.print")
def test_ipykernel_attach_bashrc_already_mounted(
    mock_print: Mock,
    mock_json_loads: Mock,
    mock_file_open: Mock,
    mock_exists: Mock,
    mock_get_kernels_dict: Mock,
) -> None:
    project_name = "existing_project"
    expected_print_message = ":warning:\t.bashrc should already been mounted in your kernel, if you are in doubt do a 'clean' followed by a 'build'"  # noqa: B907
    expected_exit_code = 0

    with unittest.TestCase().assertRaises(SystemExit) as cm:
        ipykernel_attach_bashrc(project_name)

    assert mock_get_kernels_dict.call_count == 1
    assert mock_exists.call_count == 2
    assert mock_file_open.call_count == 1
    assert mock_json_loads.call_count == 1
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
