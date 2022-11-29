"""This module contains functions used to install poetry dependecies and kernels."""
import subprocess  # noqa: S404
from pathlib import Path
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich import print

from .environment import NEXUS_SOURCE_NAME
from ssb_project_cli.ssb_project.util import create_error_log


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
        result = subprocess.run(  # noqa: S603 no untrusted input
            "poetry install".split(), capture_output=True, cwd=project_directory
        )
    if result.returncode != 0:
        calling_function = "poetry-install"
        log = str(result)

        print("Error: Something went wrong when installing packages with Poetry.")
        create_error_log(log, calling_function)
        exit(1)
    else:
        print(":white_check_mark:\tInstalled dependencies in the virtual environment")


def poetry_source_includes_source_name(
    cwd: Path, source_name: str = NEXUS_SOURCE_NAME
) -> bool:
    """Check whether this source is already added to the project.

    Args:
        cwd: Path of project to add source to
        source_name: Name of source to check

    Returns:
        True if the source exists in the list

    Raises:
        ValueError: If the process returns with error code
    """
    result = subprocess.run(  # noqa: S603 no untrusted input
        "poetry source show".split(),
        capture_output=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise ValueError(
            f'Error showing Poetry source: {result.stderr.decode("utf-8")}'
        )

    return source_name in result.stdout.decode("utf-8")


def poetry_source_remove(cwd: Path, source_name: str = NEXUS_SOURCE_NAME) -> None:
    """Remove a package installation source for this project.

    Args:
        cwd: Path of project to add source to
        source_name: Name of source to be removed

    Raises:
        ValueError: If the process returns with error code
    """
    result = subprocess.run(  # noqa: S603 no untrusted input
        f"poetry source remove {source_name}".split(),
        capture_output=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise ValueError(
            f'Error removing Poetry source: {result.stderr.decode("utf-8")}'
        )


def poetry_source_add(
    source_url: str, cwd: Path, source_name: str = NEXUS_SOURCE_NAME
) -> None:
    """Add a package installation source for this project.

    Args:
        source_url: URL of 'simple' package API of package server
        cwd: Path of project to add source to
        source_name: Name of source to add

    Raises:
        ValueError: If the process returns with error code
    """
    result = subprocess.run(  # noqa: S603 no untrusted input
        f"poetry source add --default {source_name} {source_url}".split(),
        capture_output=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise ValueError(f'Error adding Poetry source: {result.stderr.decode("utf-8")}')


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
        make_kernel_cmd = "poetry run python3 -m ipykernel install --user --name".split(
            " "
        ) + [project_name]
        result = subprocess.run(  # noqa: S603 no untrusted input
            make_kernel_cmd, capture_output=True, cwd=project_directory
        )
        if result.returncode != 0:
            calling_function = "install-kernel"
            log = str(result)

            print("Something went wrong while installing ipykernel.")
            create_error_log(log, calling_function)
            exit(1)

    print(f":white_check_mark:\tInstalled Jupyter Kernel ({project_name})")
