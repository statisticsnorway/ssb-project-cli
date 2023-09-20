"""Create command module."""
import os
import shutil
from pathlib import Path
from shutil import rmtree

import psutil
from rich import print

from ssb_project_cli.ssb_project.util import create_error_log

from ..build.build import build_project
from ..build.environment import JUPYTER_IMAGE_SPEC
from ..build.environment import running_onprem
from .github import create_github
from .github import is_github_repo
from .github import set_branch_protection_rules
from .github import valid_repo_name
from .local_repo import create_project_from_template
from .local_repo import make_and_init_git_repo
from .local_repo import make_git_repo_and_push
from .prompt import choose_login
from .prompt import request_project_description
from .repo_privacy import RepoPrivacy


def create_project(  # noqa: C901
    project_name: str,
    description: str,
    repo_privacy: RepoPrivacy,
    add_github: bool,
    github_token: str,
    working_directory: Path,
    home_path: Path,
    github_org_name: str,
    template_repo_url: str,
    checkout: str | None,
    verify_config: bool = True,
) -> None:
    """Create an SSB-project.

    Args:
        project_name: project name
        description: project description
        repo_privacy: repository visibility setting
        add_github:  Create a GitHub repository if true
        github_token: GitHub PAT
        working_directory: Current working directory
        home_path: Home Path
        github_org_name: Name of GitHub organization
        template_repo_url: The Cookiecutter template URI.
        checkout: The git reference to check against. Supports branches, tags and commit hashes.
        verify_config: Determines if gitconfig is verified.
    """
    is_memory_full()

    if not valid_repo_name(project_name):
        print(
            "Invalid repo name: Please choose a valid name. For example: 'my-fantastic-project'"
        )

        exit(1)

    if add_github and not github_token:
        github_token = choose_login(home_path)

    if add_github and not github_token:
        print("Needs GitHub token, please specify with --github-token")
        exit(1)

    if add_github and is_github_repo(github_token, project_name, github_org_name):
        print(
            f"A repo with the name {project_name} already exists on GitHub. Please choose another name."
        )
        exit(1)

    if add_github and description == "":
        description = request_project_description()

    project_directory = working_directory.joinpath(project_name)

    if project_directory.exists():
        print(
            "A project with name {!r} already exists. Please choose another name.".format(
                project_name
            )
        )
        exit(1)

    try:
        create_project_from_template(
            project_name,
            description,
            template_repo_url,
            checkout,
            working_directory,
        )
        build_project(
            project_directory,
            working_directory,
            template_repo_url,
            checkout,
            verify_config,
        )

        git_repo_dir = Path(working_directory.joinpath(project_name))
        if add_github:
            print("Creating an empty repo on Github")
            repo_url = create_github(
                github_token, project_name, repo_privacy, description, github_org_name
            )

            print("Creating a local repo, and pushing to Github")
            make_git_repo_and_push(github_token, repo_url, git_repo_dir)

            print("Setting branch protection rules")
            set_branch_protection_rules(github_token, project_name, github_org_name)

            print(f":white_check_mark:\tCreated Github repo. View it here: {repo_url}")
        else:
            make_and_init_git_repo(git_repo_dir)

        print(
            f":white_check_mark:\tCreated project ({project_name}) in the folder {project_directory}"
        )
        print(
            ":tada:\tAll done! Visit the Dapla manual to see how to use your project: https://manual.dapla.ssb.no/ssbproject.html"
        )
    except Exception as e:
        create_error_log(str(e), "create")
        delete_folder(project_directory)
    except (SystemExit, KeyboardInterrupt):
        delete_folder(project_directory)


def delete_folder(folder: Path) -> None:
    """Deletes directory if it exists.

    Args:
        folder: Path of folder to delete
    """
    if folder.is_dir():
        try:
            rmtree(folder)
        except shutil.Error as e:
            create_error_log(str(e), "delete_dir")


def is_memory_full() -> None:
    """Checks whether used memory is greater than 95% and terminates the program if that is the case."""
    # get the memory usage information
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()

    # calculate the percentage of virtual memory used
    if virtual_memory.total > 0:
        virtual_used_percent = virtual_memory.used / virtual_memory.total * 100

        # check if the percentage of used memory is greater than 95 percent
        if virtual_used_percent > 95:
            print(
                "Remaining free memory is less than 5%. Please free some memory (for example by terminating running programs) before continuing. Terminating."
            )
            exit(1)

    # calculate the percentage of swap memory used
    if swap_memory.total > 0:
        swap_used_percent = swap_memory.used / swap_memory.total * 100

        # check if the percentage of used memory is greater than 95 percent
        if swap_used_percent > 95:
            print(
                "Remaining free memory is less than 5%. Please free some memory (for example by terminating running programs) before continuing. Terminating."
            )
            exit(1)

    # Get the disk usage information for the partition hosting home directories
    if os.path.exists("/home/jovyan/"):
        home_dir = (
            "/home/jovyan/"
            if not running_onprem(JUPYTER_IMAGE_SPEC)
            else "/ssb/bruker/"
        )
        disk_usage = psutil.disk_usage(home_dir)

        # Calculate the percentage of used disk space
        disk_used_percent = disk_usage.used / disk_usage.total * 100

        # Check if the percentage of used disk space is greater than 95 percent
        if disk_used_percent > 95:
            print(
                "Remaining disk space is less than 5%. Please free some disk space before creating a new project. Terminating."
            )
            exit(1)
