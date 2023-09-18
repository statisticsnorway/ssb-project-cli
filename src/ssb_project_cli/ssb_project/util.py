"""SSB-project utils."""
import json
import logging
import os
import subprocess  # noqa: S404
import sys  # noqa: S404
import time
from pathlib import Path
from typing import Optional
from typing import Union

import jupyter_client
import tomli
from rich import print

from .settings import HOME_PATH


kernelspec_manager = jupyter_client.kernelspec.KernelSpecManager()  # type: ignore[no-untyped-call]


def set_debug_logging(home_path: Path = HOME_PATH) -> None:
    """Creates a file with log of error in the current folder.

    Args:
        home_path: path prefix to use for error logging, defaults to HOME_PATH.
    """
    error_logs_path = f"{home_path}/ssb-project-cli/.error_logs/ssb-project-debug.log"
    log_dir = os.path.dirname(error_logs_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(filename=error_logs_path, level=logging.DEBUG)


def create_error_log(
    log: str, calling_function: str, home_path: Path = HOME_PATH
) -> None:
    """Creates a file with log of error in the current folder.

    Args:
        log: The content of the error log.
        calling_function: The function in which the error occurred. Used to give a more descriptive name to error log file.
        home_path: System home path
    """
    try:
        error_logs_path = f"{home_path}/ssb-project-cli/.error_logs"
        if not os.path.exists(error_logs_path):
            os.makedirs(error_logs_path)
        filename = f"{calling_function}-error-{int(time.time())}.txt"
        with open(f"{error_logs_path}/{filename}", "w+") as f:
            f.write(log)
            print(f"Detailed error information saved to {error_logs_path}/{filename}")
            print(
                f"You can find the full debug log here {error_logs_path}/ssb-project-debug.log"
            )
            print(
                f"❗️You can try deleting '.poetry/cache' in your project directory or '{home_path}/.cache/pypoetry'. Cache could be causing problems"
            )
    except Exception as e:
        print(f"Error while attempting to write the log file: {e}")


def execute_command(
    command: Union[str, list[str]],
    command_shortname: str,
    success_desc: Optional[str] = None,
    failure_desc: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess[bytes]:
    """Execute command and handle failure/success cases.

    Args:
        command: The command to be executed. For example "poetry install".
        command_shortname: For example: "poetry-install". Used to create descriptive error log file.
        success_desc: For example: "Poetry install ran successfully".
        failure_desc: For example: "Something went wrong while running poetry install".
        cwd: The current working directory.

    Returns:
        The result of the subprocess.
    """
    if isinstance(command, str):
        command = command.split(" ")
    result = subprocess.run(  # noqa S603
        command,
        capture_output=True,
        cwd=cwd,
    )

    if result.returncode != 0:
        calling_function = command_shortname
        log = str(result)
        if failure_desc:
            print(failure_desc)
        else:
            print("Error while running: " + " ".join(command))
        create_error_log(log, calling_function)
        sys.exit(1)
    else:
        if success_desc:
            print(success_desc)

    return result


def get_kernels_dict() -> dict[str, dict[str, str]]:
    """Gets installed kernel specifications.

    Returns:
        kernel_dict: Dictionary of installed kernel specifications
    """
    return kernelspec_manager.get_all_specs()  # type: ignore


def remove_kernel_spec(kernel_name: str) -> None:
    """Remove a kernel spec."""
    kernelspec_manager.remove_kernel_spec(kernel_name)  # type: ignore[no-untyped-call]


def get_project_name_and_root_path(
    project_path: Path | None = None,
) -> tuple[str | None, Path | None]:
    """Get the name and root of the project.

    - First source: `.cruft.json`
    - Second source: `pyproject.toml`
    - Final fallback: project root directory name.

    Args:
        project_path: Optionally supply a path to the project. If not supplied, use the current working directory.

    Returns:
        project_name: The name of the project.
        project_root: Path of the root directory of the project.
    """
    cruft_json_name = ".cruft.json"
    pyproject_name = "pyproject.toml"
    origin = project_path or Path.cwd()
    if not origin.exists():
        return None, None
    paths = [origin]
    # List of current path and all parents up to the filesystem root
    paths.extend(origin.parents)

    for path in paths:
        if {i.name for i in path.iterdir()}.intersection(
            {cruft_json_name, pyproject_name, ".git"}
        ):
            try:
                # Attempt to source from Cruft first
                name = json.loads((path / cruft_json_name).read_text())["context"][
                    "cookiecutter"
                ]["project_name"]
                return (
                    name,
                    path,
                )
            except (KeyError, FileNotFoundError, json.JSONDecodeError):
                # Fall back to pyproject.toml
                try:
                    name = tomli.loads((path / pyproject_name).read_text())["tool"][
                        "poetry"
                    ]["name"]
                    return (
                        name,
                        path,
                    )
                except (KeyError, FileNotFoundError):
                    # Final fall back to project root directory name
                    return path.name, path
    return None, None
