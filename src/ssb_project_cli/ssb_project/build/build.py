"""Build command module."""
from pathlib import Path

from .environment import JUPYTER_IMAGE_SPEC
from .environment import PIP_INDEX_URL
from .environment import running_onprem
from .poetry import install_ipykernel
from .poetry import poetry_install
from .poetry import poetry_source_add
from .poetry import poetry_source_includes_source_name
from .poetry import poetry_source_remove
from rich import print


def build_project(path: str, working_directory: Path) -> None:
    """Installs dependencies and kernel for a given project.

    Args:
        path: Path to project
        working_directory: working directory
    """
    project_directory = Path(path)

    if path == "":
        project_name = working_directory.name
        project_directory = working_directory
    else:
        project_name = project_directory.name

    if running_onprem(JUPYTER_IMAGE_SPEC):
        print(
            ":twisted_rightwards_arrows:\tDetected onprem environment, using proxy for package installation"
        )
        poetry_source_add(PIP_INDEX_URL, project_directory)
    elif poetry_source_includes_source_name(project_directory):
        print(
            ":twisted_rightwards_arrows:\tDetected non-onprem environment, removing proxy for package installation"
        )
        poetry_source_remove(project_directory)

    poetry_install(project_directory)
    install_ipykernel(project_directory, project_name)
