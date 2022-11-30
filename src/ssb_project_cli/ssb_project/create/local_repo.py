"""This module contains functions used to set up a local git repository with ssb-project."""
import json
import subprocess  # noqa: S404
from datetime import datetime
from pathlib import Path
from typing import Optional

from git import Repo  # type: ignore[attr-defined]
from github import Github

from ssb_project_cli.ssb_project.create import temp_git_repo
from ssb_project_cli.ssb_project.create.prompt import request_name_email


def create_project_from_template(
    project_name: str,
    description: str,
    template_repo_url: str,
    template_reference: str,
    working_directory: Path,
    license_year: Optional[str] = None,
) -> Path:
    """Creates a project from CookiCutter template.

    Args:
        project_name: Name of project
        description: Project description
        license_year: Year to be inserted into the LICENSE
        template_repo_url: URL for the chosen template
        template_reference: Git reference to the template repository
        working_directory: Working directory

    Returns:
        Path: Path of project.
    """
    project_dir = working_directory.joinpath(project_name)
    if project_dir.exists():
        print(
            f"A project with name '{project_name}' already exists. Please choose another name."
        )
        exit(1)

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
    quoted = json.dumps(template_info).replace('"', '"')

    argv = [
        "cruft",
        "create",
        template_repo_url,
        "--no-input",
        "--checkout",
        template_reference,
        "--extra-context",
        quoted,
    ]

    subprocess.run(  # noqa: S603 no untrusted input
        argv, check=True, cwd=working_directory
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

    github_username = Github(github_token).get_user().login
    credential_url = mangle_url(github_url, github_token)
    username_url = mangle_url(github_url, github_username)

    with temp_git_repo.TempGitRemote(repo, credential_url, username_url):
        repo.git.push("--set-upstream", "origin", "main")


def mangle_url(url: str, mangle_name: str) -> str:
    """Create url mangled with a string: credential or username."""
    mangle_name = mangle_name + "@"
    split_index = url.find("//") + 2
    return url[:split_index] + mangle_name + url[split_index:]
