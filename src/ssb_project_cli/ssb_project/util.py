"""SSB-project utils."""
import os
import subprocess  # noqa: S404
import time
from pathlib import Path
from typing import Optional
from typing import Union

from rich import print

from .settings import HOME_PATH


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
        exit(1)
    else:
        print(success_desc)

    return result
