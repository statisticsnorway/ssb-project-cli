"""This module contains prompts used when creating a ssb-project."""
from pathlib import Path

import questionary
import typer

from .github import get_github_pat


def request_name_email() -> tuple[str, str]:
    """Requests name and email from user.

    Returns:
        tuple[str, str]: User supplied name and email
    """
    name = typer.prompt("Enter your full name: ")
    email = typer.prompt("Enter your email: ")
    return name, email


def request_project_description() -> str:
    """Prompts the user for a project description.

    Continues to prompt the user until a non-empty string is supplied.

    Returns:
         str: Project description
    """
    description: str = typer.prompt("Project description")

    if description == "":
        description = request_project_description()

    return description


def choose_login(path: Path) -> str:
    """Asks the user to pick between stored GitHub usernames.

    If GitHub credentials are not found users is promoted to input PAT.

    Args:
        path: Path to folder containing GitHub credentials

    Returns:
        str: GitHub personal access token
    """
    user_token_dict: dict[str, str] = get_github_pat(path)

    if len(user_token_dict) == 1:
        return list(user_token_dict.values())[0]
    if user_token_dict:
        choice = questionary.select(
            "Select your GitHub account:", choices=user_token_dict.keys()  # type: ignore
        ).ask()
        return user_token_dict[choice]
    else:
        pat: str = questionary.password(
            "Enter your GitHub personal access token:"
        ).ask()
        return pat
