"""This module contains prompts used when building a ssb-project."""
from pathlib import Path

import typer
from ssb_project_cli.ssb_project.build.environment import reset_global_gitconfig
from ssb_project_cli.ssb_project.create.local_repo import (
    reset_project_git_configuration,
)


def confirm_fix_ssb_git_config(
    project_name: str,
    template_repo_url: str,
    checkout: str | None,
    project_directory: Path,
    valid_global_git_config: bool,
    valid_project_git_config: bool,
) -> None:
    """Prompts user for conformation regarding reset of git configuration files.

    Args:
        project_name: Name of project
        template_repo_url: URL for the chosen template
        checkout: The git reference to check against. Supports branches, tags and commit hashes.
        project_directory: Directory of the project.
        valid_global_git_config: True if global git is configured according to company policy.
        valid_project_git_config:True if local git files are configured according to company policy.
    """
    valid_global_git_config_tuple = (".gitconfig", "")
    valid_project_git_config_tuple = (".gitattributes and .gitignore", "")
    changed_files = f"{valid_global_git_config_tuple[valid_global_git_config]} {valid_project_git_config_tuple[valid_project_git_config]}"

    # Default is set to None makes typer repeat until input y/n is given.
    if typer.confirm(
        f"\n\tWould you like to reset your Git configuration to the SSB recommended defaults?\n\tThis action will override changes you have made to: {changed_files}",
        default=None,
    ):
        print()  # Formatting print
        if not valid_global_git_config:
            reset_global_gitconfig()
        if not valid_project_git_config:
            reset_project_git_configuration(
                project_name, template_repo_url, checkout, project_directory
            )
