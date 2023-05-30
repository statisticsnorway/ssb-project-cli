"""This module contains functions used to install poetry dependecies and kernels."""
import os
from pathlib import Path
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich import print

from .environment import NEXUS_SOURCE_NAME
from ssb_project_cli.ssb_project.util import execute_command


def poetry_install(project_directory: Path) -> None:
    """Call poetry install in project_directory.

    Args:
        project_directory: Path of project
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Installing dependencies... This may take a few minutes",
            total=None,
        )

        execute_command(
            "poetry install".split(" "),
            "poetry-install",
            ":white_check_mark:\tInstalled dependencies in the virtual environment",
            "Error: Something went wrong when installing packages with Poetry.",
            project_directory,
        )


def poetry_source_includes_source_name(
    cwd: Path, source_name: str = NEXUS_SOURCE_NAME
) -> bool:
    """Check whether this source is already added to the project.

    Args:
        cwd: Path of project to add source to
        source_name: Name of source to check

    Returns:
        True if the source exists in the list
    """
    result = execute_command(
        "poetry source show".split(" "),
        "poetry-source-show",
        "",
        "Error showing Poetry source.",
        cwd=cwd,
    )

    return source_name in result.stdout.decode("utf-8")


def poetry_source_remove(
    cwd: Path, lock_update: bool = True, source_name: str = NEXUS_SOURCE_NAME
) -> None:
    """Remove a package installation source for this project.

    Args:
        cwd: Path of project to add source to
        lock_update: Bool used to decide whether to run update_lock
        source_name: Name of source to be removed
    """
    print("Removing Poetry source...")
    execute_command(
        f"poetry source remove {source_name}".split(" "),
        "source-remove",
        "Poetry source successfully removed!",
        "Failed to remove Poetry source.",
        cwd=cwd,
    )
    if lock_update:
        update_lock(cwd)


def poetry_source_add(
    source_url: str, cwd: Path, source_name: str = NEXUS_SOURCE_NAME
) -> None:
    """Add a package installation source for this project.

    Args:
        source_url: URL of 'simple' package API of package server
        cwd: Path of project to add source to
        source_name: Name of source to add
    """
    print("Adding package installation source for poetry...")
    execute_command(
        f"poetry source add --priority=default {source_name} {source_url}".split(" "),
        "poetry-source-add",
        "Poetry source successfully added!",
        "Failed to add poetry source.",
        cwd=cwd,
    )

    # If the lock is created off-prem, we need to refresh the lock.
    if should_update_lock_file(source_url, cwd):
        update_lock(cwd)


def update_lock(cwd: Path) -> None:
    """Runs poetry lock --no-update command in CWD.

    Args:
        cwd: Path of project to add source to.
    """
    print("Refreshing lock file...")
    execute_command(
        "poetry lock --no-update".split(" "),
        "update_lock",
        "Poetry successfully refreshed lock file!",
        "Poetry failed to refresh lock file.",
        cwd=cwd,
    )


def should_update_lock_file(source_url: str, cwd: Path) -> bool:
    """Checks if poetry.lock exists and if nexus source is set there.

    Args:
        source_url: URL of 'simple' package API of package server
        cwd: Path of project to add source to
    Returns:
        True if source url is not set in lock file, else False.
    """
    lock_file_path = cwd / Path("poetry.lock")
    if os.path.isfile(lock_file_path):
        with open(lock_file_path) as lock_file:
            if source_url in lock_file.read():
                return False
    else:
        return False

    return True


def install_ipykernel(project_directory: Path, project_name: str) -> None:
    """Installs ipykernel.

    Args:
        project_directory: Path of project
        project_name: Name of project
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Installing Jupyter kernel...", total=None)
        kernel_cmd = f"poetry run python3 -m ipykernel install --user --name {project_name}".split(
            " "
        )

        execute_command(
            kernel_cmd,
            "install-ipykernel",
            f":white_check_mark:\tInstalled Jupyter Kernel ({project_name})",
            "Something went wrong while installing ipykernel.",
            project_directory,
        )
