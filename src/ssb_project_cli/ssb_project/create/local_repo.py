"""This module contains functions used to set up a local git repository with ssb-project."""
import shutil
import subprocess  # noqa: S404
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import cruft  # type: ignore[import]
from git import Repo  # type: ignore[attr-defined]
from rich import print

from ssb_project_cli.ssb_project.create import temp_git_repo
from ssb_project_cli.ssb_project.create.github import (
    get_environment_specific_github_object,
)
from ssb_project_cli.ssb_project.create.github import get_github_username
from ssb_project_cli.ssb_project.create.prompt import request_name_email
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_REPO_URL
from ssb_project_cli.ssb_project.util import create_error_log


def create_project_from_template(
    project_name: str,
    description: str,
    template_repo_url: str,
    checkout: str | None,
    working_directory: Path,
    license_year: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    override_dir: Optional[Path] = None,
) -> Path:
    """Creates a project from CookieCutter template.

    Args:
        project_name: Name of project
        description: Project description
        license_year: Year to be inserted into the LICENSE
        template_repo_url: The Cookiecutter template URI.
        checkout: The git reference to check against. Supports branches, tags and commit hashes.
        working_directory: Working directory
        name: Optional name of project owner
        email: Optional email of project owner
        override_dir: Used to hard set working_directory.

    Returns:
        Path: Path of project.
    """
    if override_dir is None:
        project_dir = working_directory.joinpath(project_name)
    else:
        project_dir = override_dir

    if not (name and email):
        name, email = extract_name_email()
        if not (name and email):
            name, email = request_name_email()

    template_info = {
        "project_name": project_name,
        "description": description,
        "full_name": name,
        "email": email,
        "license_year": license_year or str(datetime.now().year),
    }
    cruft.create(
        template_git_url=template_repo_url,
        checkout=checkout,
        no_input=(template_repo_url == STAT_TEMPLATE_REPO_URL),
        extra_context=template_info,
    )

    return project_dir


def extract_name_email() -> tuple[str, str]:
    """Grabs email and name from git config.

    Returns:
        name: Value of user.name from git config element
        email: Value of user.email from git config element
    """
    name = get_gitconfig_element("user.name")
    email = get_gitconfig_element("user.email")
    return name, email


def get_gitconfig_element(element: str) -> str:
    """Grabs a property from git config.

    Args:
        element: Name of the git config element retrive

    Returns:
        str: Value of git config element
    """
    cmd = ["git", "config", "--get", element]
    result = subprocess.run(  # noqa: S603 no untrusted input
        cmd, stdout=subprocess.PIPE, encoding="utf-8"
    )

    return result.stdout.strip()


def make_and_init_git_repo(repo_dir: Path) -> Repo:
    """Makes and pushes a GitHub repository.

    Inits a local repository, adds all files and commits.

    Args:
        repo_dir: Path to local Repository

    Returns:
        Repo: Repository
    """
    repo = Repo.init(repo_dir)
    repo.git.add("-A")
    repo.index.commit("Initial commit")
    repo.git.branch("-M", "main")
    return repo


def make_git_repo_and_push(github_token: str, github_url: str, repo_dir: Path) -> None:
    """Makes and pushes a GitHub repository.

    Inits a local repository and tries to push it to GitHub,
     for more information see TempGitRemote.

    Args:
        github_token: GitHub personal access token
        github_url: Repository url
        repo_dir: Path to local Repository
    """
    repo = make_and_init_git_repo(repo_dir)

    github_username = get_github_username(
        get_environment_specific_github_object(github_token), github_token
    )
    credential_url = mangle_url(github_url, github_token)
    username_url = mangle_url(github_url, github_username)

    with temp_git_repo.TempGitRemote(repo, credential_url, username_url):
        repo.git.push("--set-upstream", "origin", "main")


def mangle_url(url: str, mangle_name: str) -> str:
    """Create url mangled with a string: credential or username."""
    mangle_name = mangle_name + "@"
    split_index = url.find("//") + 2
    return url[:split_index] + mangle_name + url[split_index:]


def reset_project_git_configuration(
    project_name: str,
    template_repo_url: str,
    checkout: str | None,
    project_directory: Path,
) -> None:
    """Overrides .gitattributes and .gitignore inn a given project directory.

    Args:
        project_name: Name of project.
        template_repo_url: URL for the chosen template.
        checkout: The git reference to check against. Supports branches, tags and commit hashes.
        project_directory: Directory of the project.
    """
    files = [".gitattributes", ".gitignore"]
    try:
        with tempfile.TemporaryDirectory() as tempdir:
            create_project_from_template(
                project_name,
                "",
                template_repo_url,
                checkout,
                Path(tempdir),
                name=None,
                email=None,
                override_dir=Path(tempdir),
            )
            for file in files:
                shutil.copy(
                    tempdir / Path(project_name) / Path(file),
                    project_directory / Path(file),
                )
    except Exception as e:
        print(":x:\tCould not restore .gitattributes .gitignore.")
        create_error_log(f"{e}", "reset_project_git_configuration")
    print(":white_check_mark:\tRestored recommended .gitattributes .gitignore.")
