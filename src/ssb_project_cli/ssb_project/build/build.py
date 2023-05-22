"""Build command module."""
from pathlib import Path

import kvakk_git_tools.validate_ssb_gitconfig  # type: ignore

from .environment import JUPYTER_IMAGE_SPEC, verify_local_config
from .environment import PIP_INDEX_URL
from .environment import running_onprem
from .poetry import install_ipykernel
from .poetry import poetry_install
from .poetry import poetry_source_add
from .poetry import poetry_source_includes_source_name
from .poetry import poetry_source_remove
from rich import print

from .prompt import confirm_fix_ssb_git_config


def build_project(
    path: Path,
    working_directory: Path,
    template_repo_url: str,
    template_reference: str,
    verify_config: bool = True,
) -> None:
    """Installs dependencies and kernel for a given project.

    Args:
        path: Path to project
        working_directory: working directory
        template_repo_url: Template repository url
        template_reference: Template reference
        verify_config: Determines if gitconfig is verified.
    """
    if path == "":
        project_name = working_directory.name
        project_directory = working_directory
    else:
        project_name = path.absolute().name
        project_directory = working_directory / path

    if not (project_directory / "pyproject.toml").is_file():
        print(
            f":x:\tProject directory: {project_directory} is not a valid SSB-project, pyproject.toml is missing."
        )
        exit(1)
    if verify_config:
        valid_global_git_config = kvakk_git_tools.validate_git_config()
        valid_project_git_config = verify_local_config(
            template_repo_url,
            template_reference,
            cwd=str(working_directory / project_directory),
        )
        if not valid_global_git_config or not valid_project_git_config:
            print(
                ":x:\tYour project's Git configuration does not follow SSB recommendations,\n:x:\twhich may result in sensitive data being pushed to GitHub."
            )
            confirm_fix_ssb_git_config(
                project_name,
                template_repo_url,
                template_reference,
                project_directory,
                valid_global_git_config,
                valid_project_git_config,
            )

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
