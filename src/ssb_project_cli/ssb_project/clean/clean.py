"""Clean command module."""
import sys
from pathlib import Path

import questionary
from rich import print

from ssb_project_cli.ssb_project.util import execute_command
from ssb_project_cli.ssb_project.util import get_kernels_dict
from ssb_project_cli.ssb_project.util import remove_kernel_spec


def clean_project(project_name: str) -> None:
    """Removes the kernel and/or virtual environment of an SSB-project.

    Args:
        project_name: Project name
    """
    clean_venv()

    kernels = get_kernels_dict()

    if project_name not in kernels:
        print(
            "Could not find kernel {!r}. Is the project name spelled correctly?".format(
                project_name
            )
        )

        sys.exit(1)

    confirmation = questionary.confirm(
        "Are you sure you want to delete the kernel {!r}. This action will delete the kernel associated with the virtual environment and leave all other files untouched.".format(
            project_name
        )
    ).ask()

    if not confirmation:
        sys.exit(1)

    print(
        f"Deleting kernel {project_name}...If you wish to also delete the project files, you can do so manually."
    )

    remove_kernel_spec(project_name)


def clean_venv() -> None:
    """Removes the virtual environment for project if it exists in current directory. If not, user is prompted for path to ssb project."""
    confirm = questionary.confirm(
        "Do you also wish to delete the virtual environment for this project?"
    ).ask()
    if confirm:
        if Path(".venv").is_dir():
            clean_venv_cmd = "rm -rf .venv"

            execute_command(
                clean_venv_cmd,
                "clean-virtualenv",
                "Virtual environment successfully removed!",
                "Something went wrong while removing virtual environment in current directory. A log of the issue was created...",
                None,
            )

        else:
            print("No virtual environment found in current directory. Skipping...")
