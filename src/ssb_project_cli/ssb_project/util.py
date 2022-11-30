"""SSB-project utils."""
import os
import time
from pathlib import Path

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
