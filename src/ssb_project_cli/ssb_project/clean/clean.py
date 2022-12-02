"""Clean command module."""
import subprocess  # noqa: S404
from pathlib import Path

import questionary
from rich import print

from ssb_project_cli.ssb_project.util import execute_command


def clean_project(project_name: str) -> None:
    """Removes the kernel and/or virtual environment of an SSB-project.

    Args:
        project_name: Project name
    """
    clean_venv()

    kernels = get_kernels_dict()

    if project_name not in kernels:
        print(
            f'Could not find kernel "{project_name}". Is the project name spelled correctly?'
        )

        exit(1)

    confirmation = questionary.confirm(
        f"Are you sure you want to delete the kernel '{project_name}'. This action will delete the kernel associated with the virtual environment and leave all other files untouched."
    ).ask()

    if not confirmation:
        exit(1)

    print(
        f"Deleting kernel {project_name}...If you wish to also delete the project files, you can do so manually."
    )

    clean_cmd = f"jupyter kernelspec remove -f {project_name}".split(" ")

    execute_command(
        clean_cmd,
        "clean-cmd",
        f"Deleted Jupyter kernel {project_name}.",
        "Error: Something went wrong while removing the jupyter kernel.",
        None,
    )


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
        if len(line.split(" ")) == 2:
            k, v = line.split(" ")
            kernel_dict[k] = v
    return kernel_dict


def clean_venv() -> None:
    """Removes the virtual environment for project if it exists in current directory. If not, user is prompted for path to ssb project."""
    confirm = questionary.confirm(
        "Do you also wish to delete the virtual environment for this project?"
    ).ask()
    if confirm:
        if Path(".venv").is_dir():
            clean_venv_cmd = "rm -rf .venv".split(" ")

            execute_command(
                clean_venv_cmd,
                "clean-virtualenv",
                "Virtual environment successfully removed!",
                "Something went wrong while removing virtual environment in current directory. A log of the issue was created...",
                None,
                True,
            )

        else:
            print("No virtual environment found in current directory...")
            path = questionary.path(
                "Please provide the path to the ssb project you wish to delete the virtual environment for:"
            ).ask()
            if Path(f"{path}/.venv").is_dir():
                clean_venv_cmd = f"rm -rf {path}/.venv".split(" ")

                execute_command(
                    clean_venv_cmd,
                    "clean-virtualenv",
                    "Virtual environment successfully removed!",
                    "Something went wrong while removing virtual environment at provided path. A log of the issue was created...",
                    None,
                    True,
                )

            else:
                print("No virtual environment found at that path. Skipping...")

    else:
        print(
            "Skipping removal of virtual environment. The virtual environment can also be removed manually by deleting the .venv folder in your ssb project directory."
        )
