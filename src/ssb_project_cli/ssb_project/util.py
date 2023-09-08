"""SSB-project utils."""
import logging
import os
import subprocess  # noqa: S404
import sys  # noqa: S404
import time
from pathlib import Path
from typing import Optional
from typing import Union

from rich import print

from .settings import HOME_PATH


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
            f.close()
    except Exception as e:
        print(f"Error while attempting to write the log file: {e}")


def execute_command(
    command: Union[str, list[str]],
    command_shortname: str,
    success_desc: Optional[str],
    failure_desc: str,
    cwd: Optional[Path],
    shell: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    """Execute command and handle failure/success cases.

    Args:
        command: The command to be executed. For example "poetry install".
        command_shortname: For example: "poetry-install". Used to create descriptive error log file.
        success_desc: For example: "Poetry install ran successfully".
        failure_desc: For example: "Something went wrong while running poetry install".
        cwd: The current working directory.
        shell: Setting the shell argument to a true value causes subprocess to spawn an intermediate shell process.

    Returns:
        The result of the of the subprocess.

    """
    if cwd:
        result = subprocess.run(
            command,
            capture_output=True,
            cwd=cwd,
            shell=shell,  # noqa: S60 no untrusted input
        )
    else:
        result = subprocess.run(
            command, capture_output=True, shell=shell  # noqa: S602 no untrusted input
        )

    if result.returncode != 0:
        calling_function = command_shortname
        log = str(result)
        print(failure_desc)
        create_error_log(log, calling_function)
        sys.exit(1)
    else:
        print(success_desc)

    return result


def get_kernels_dict() -> dict[str, str]:
    """Makes a dictionary of installed kernel specifications.

    Returns:
        kernel_dict: Dictionary of installed kernel specifications
    """
    kernels_process = subprocess.run(  # noqa S607
        ["jupyter", "kernelspec", "list"], capture_output=True
    )
    kernels_str = ""
    if kernels_process.returncode == 0:
        kernels_str = kernels_process.stdout.decode("utf-8")
    else:
        print("An error occured while looking for installed kernels.")
        exit(1)
    kernel_dict = {}
    for kernel in kernels_str.split("\n")[1:]:
        line = " ".join(kernel.strip().split())
        line = line.replace("%s ", "").strip()
        if len(line.split(" ")) == 2:
            k, v = line.split(" ")
            kernel_dict[k] = v
    return kernel_dict
