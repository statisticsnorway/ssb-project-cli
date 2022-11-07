"""Command-line-interface for project-operations in dapla-jupterlab."""
import json
import os
import re
import subprocess  # noqa: S404
import time
from enum import Enum
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from traceback import format_exc
from types import TracebackType
from typing import Optional
from typing import Type

import questionary
import typer
from git import Repo  # type: ignore[attr-defined]
from github import BadCredentialsException
from github import Github
from github import GithubException
from rich.console import Console
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from .environment import JUPYTER_IMAGE_SPEC
from .environment import PIP_INDEX_URL


# Don't print with color, it's difficult to read when run in Jupyter
console = Console(color_system=None)
print = console.print

app = typer.Typer(
    help="Usage instructions: https://statisticsnorway.github.io/dapla-manual/ssb-project.html",
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,  # Locals can contain sensitive information
)
GITHUB_ORG_NAME = "statisticsnorway"
NEXUS_SOURCE_NAME = "nexus"
debug_without_create_repo = False
HOME_PATH = Path.home()
CURRENT_WORKING_DIRECTORY = Path.cwd()
STAT_TEMPLATE_REPO_URL = (
    "https://github.com/statisticsnorway/stat-hurtigstart-template-master"
)
STAT_TEMPLATE_DEFAULT_REFERENCE = "0.2.0"


def running_onprem(image_spec: str) -> bool:
    """Are we running in Jupyter on-prem?

    Args:
        image_spec: Value of the JUPYTER_IMAGE_SPEC environment variable

    Returns:
        True if running on-prem, else False.
    """
    return "onprem" in image_spec


def is_github_repo(token: str, repo_name: str) -> bool:
    """Checks if a Repository already exists in the organization.

    Args:
        repo_name:  Repository name
        token: GitHub personal access token.

    Returns:
        True if the repository exists, else false.
    """
    try:
        Github(token).get_repo(f"{GITHUB_ORG_NAME}/{repo_name}")
    except ValueError:
        typer.echo(
            "The provided Github credentials are invalid. Please check that your personal access token is not expired."
        )
        exit(1)
    except GithubException:
        return False
    else:
        return True


def mangle_url(url: str, mangle_name: str) -> str:
    """Create url mangled with a string: credential or username."""
    mangle_name = mangle_name + "@"
    split_index = url.find("//") + 2
    return url[:split_index] + mangle_name + url[split_index:]


class TempGitRemote:
    """Context manager class for creating and cleaning up a temporary git remote."""

    def __init__(self, repo: Repo, temp_url: str, restore_url: str) -> None:
        """Inits a TempGitRepo.

        Args:
            repo: Git repository
            temp_url: Temp url
            restore_url: Restore url
        """
        self.repo = repo
        self.temp_url = temp_url
        self.restore_url = restore_url

    def __enter__(self) -> None:
        """Deletes remote in Repository and creates remote at temp_url."""
        for remote in self.repo.remotes:
            self.repo.delete_remote(remote)
        self.origin = self.repo.create_remote("origin", self.temp_url)
        return None

    # Look up
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Deletes remote self.origin and creates a remote named origin with an url."""
        self.repo.delete_remote(self.origin)
        self.repo.create_remote("origin", self.restore_url)


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

    Inits a local repository and tries to push it to github,
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

    with TempGitRemote(repo, credential_url, username_url):
        repo.git.push("--set-upstream", "origin", "main")


def set_branch_protection_rules(github_token: str, repo_name: str) -> None:
    """Sets branch default protection rules.

    The following rules are set:
    Main branch pull requests requires a minimum of 1 reviewer.
    Reviews that are no longer valid can be dismissed.
    When you dismiss a review, you must add a comment explaining why you dismissed it.

    Args:
        github_token: GitHub personal access token
        repo_name: name of repository
    """
    repo = Github(github_token).get_repo(f"{GITHUB_ORG_NAME}/{repo_name}")
    repo.get_branch("main").edit_protection(
        required_approving_review_count=1, dismiss_stale_reviews=True
    )


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


def request_name_email() -> tuple[str, str]:
    """Requests name and email from user.

    Returns:
        tuple[str, str]: User supplied name and email
    """
    name = typer.prompt("Enter full name: ")
    email = typer.prompt("Enter email: ")
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


def extract_name_email() -> tuple[str, str]:
    """Grabs email and name from git config.

    Returns:
        name: Value of user.name from git config element
        email: Value of user.email from git config element
    """
    name = get_gitconfig_element("user.name")
    email = get_gitconfig_element("user.email")
    return name, email


def create_project_from_template(
    project_name: str,
    description: str,
    temp_dir: Path,
    template_repo_url: str = STAT_TEMPLATE_REPO_URL,
    template_reference: str = STAT_TEMPLATE_DEFAULT_REFERENCE,
) -> Path:
    """Creates a project from CookiCutter template.

    Args:
        project_name: Name of project
        description: Project description
        temp_dir: Temporary directory path
        template_repo_url: URL for the chosen template
        template_reference: Git reference to the template repository

    Returns:
        Path: Path of project.
    """
    home_dir = CURRENT_WORKING_DIRECTORY
    project_dir = home_dir.joinpath(project_name)
    if project_dir.exists():
        typer.echo(
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

    subprocess.run(argv, check=True, cwd=temp_dir)  # noqa: S603 no untrusted input

    return project_dir


class RepoPrivacy(str, Enum):
    """Class with predefined privacy enums."""

    internal = "internal"
    private = "private"
    public = "public"


@app.command()
def create(
    project_name: str = typer.Argument(..., help="Project name"),  # noqa: B008
    description: str = typer.Argument(  # noqa: B008
        "", help="A short description of your project"
    ),
    repo_privacy: RepoPrivacy = typer.Argument(  # noqa: B008
        RepoPrivacy.internal, help="Visibility of the Github repo"
    ),
    add_github: bool = typer.Option(  # noqa: B008
        False,
        "--github",
        help="Create the repo on Github as well",
    ),
    github_token: str = typer.Option(  # noqa: B008
        "",
        help="Your Github Personal Access Token, follow these instructions to create one: https://statisticsnorway.github.io/dapla-manual/ssb-project.html#personal-access-token-pat",
    ),
) -> None:
    """:sparkles:\tCreate a project locally, and optionally on Github with the flag --github. The project will follow SSB's best practice for development."""
    if not valid_repo_name(project_name):
        typer.echo(
            "Invalid repo name: Please choose a valid name. For example: 'my-fantastic-project'"
        )

        exit(1)

    if add_github and not github_token:
        github_token = choose_login()

    if add_github and not github_token:
        typer.echo("Needs GitHub token, please specify with --github-token")
        exit(1)

    if not debug_without_create_repo:
        if add_github and is_github_repo(github_token, project_name):
            typer.echo(
                f"A repo with the name {project_name} already exists on GitHub. Please choose another name."
            )
            exit(1)

    if add_github and description == "":
        description = request_project_description()

    with TemporaryDirectory() as temp_dir:

        create_project_from_template(project_name, description, Path(temp_dir))

        git_repo_dir = Path(Path(temp_dir).joinpath(project_name))
        if add_github:
            print("Creating an empty repo on Github")
            repo_url = create_github(
                github_token, project_name, repo_privacy, description
            )

            print("Creating a local repo, and pushing to Github")
            make_git_repo_and_push(github_token, repo_url, git_repo_dir)

            print("Setting branch protection rules")
            set_branch_protection_rules(github_token, project_name)

            print(f":white_check_mark:\tCreated Github repo. View it here: {repo_url}")
        else:
            make_and_init_git_repo(git_repo_dir)

        project_directory = CURRENT_WORKING_DIRECTORY / project_name
        temp_project_directory = Path(temp_dir) / project_name

        build(path=str(temp_project_directory))
        copytree(temp_project_directory, project_directory)
        print(
            f":white_check_mark:\tCreated project ({project_name}) in the folder {project_directory}"
        )
        print(
            ":tada: All done! Visit the Dapla manual to see how to use your project: https://statisticsnorway.github.io/dapla-manual/ssb-project.html"
        )


@app.command()
def build(
    path: str = typer.Argument(  # noqa: B008
        "",
        help="Project path",
    ),
) -> None:
    """:wrench:\tCreate a virtual environment and corresponding Jupyter kernel. Runs in the current folder if no arguments are supplied."""
    project_directory = Path(path)

    if path == "":
        project_name = CURRENT_WORKING_DIRECTORY.name
        project_directory = CURRENT_WORKING_DIRECTORY
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


def get_github_pat() -> dict[str, str]:
    """Gets GitHub users and PAT from .gitconfig and .netrc.

    Returns:
        dict[str, str]: A dict with user as key and PAT as value.
    """
    user_token_dict = get_github_pat_from_gitcredentials() | get_github_pat_from_netrc()

    if not user_token_dict:
        typer.echo(
            "Could not find your github token. Please add it manually with the --github-token <TOKEN> option."
        )
        exit(1)
    return user_token_dict


def get_github_pat_from_gitcredentials() -> dict[str, str]:
    """Gets GitHub users and PAT from .gitconfig."""
    git_credentials_file = HOME_PATH.joinpath(Path(".git-credentials"))
    user_token_dict: dict[str, str] = {}

    if not git_credentials_file.exists():
        return user_token_dict

    with open(git_credentials_file) as f:
        lines = f.readlines()
        for line in lines:
            p = re.compile("https://([A-Za-z0-9_-]+):([A-Za-z0-9_]+)@github.com")
            res = p.match(line)
            print(line)

            if res:
                user = res.group(1)
                token = res.group(2)
                user_token_dict[user] = token

    return user_token_dict


def get_github_pat_from_netrc() -> dict[str, str]:
    """Gets GitHub users and PAT from .netrc.

    Returns:
        dict[str, str]: A dict with user as key and PAT as value.
    """
    credentials_netrc_file = HOME_PATH.joinpath(Path(".netrc"))
    user_token_dict: dict[str, str] = {}

    with open(credentials_netrc_file) as f:
        lines = f.readlines()
        for line in lines:
            p = re.compile(
                "machine github.com login ([A-Za-z0-9_-]+) password ([A-Za-z0-9_]+)"
            )
            res = p.match(line)

            if res:
                user = res.group(1)
                token = res.group(2)
                user_token_dict[user] = token

    return user_token_dict


def valid_repo_name(name: str) -> bool:
    """Checks if the supplied name is suitable for a git repo.

    Accepts:
     - ASCII characters upper and lower case
     - Underscores
     - Hyphens
     - 3 characters or longer

    Args:
        name: Supplied repo name

    Returns:
        bool: True if the string is a valid repo name
    """
    return len(name) >= 3 and re.fullmatch("^[a-zA-Z0-9-_]+$", name) is not None


def choose_login() -> str:
    """Asks the user to pick between stored GitHub usernames.

    If GitHub credentials are not found users is promoted to input PAT.

    Returns:
        str: GitHub personal access token
    """
    user_token_dict: dict[str, str] = get_github_pat()
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

            typer.echo("Something went wrong while installing ipykernel.")
            create_error_log(log, calling_function)
            exit(1)

    print(f":white_check_mark:\tInstalled Jupyter Kernel ({project_name})")


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

        typer.echo("Error: Something went wrong when installing packages with Poetry.")
        create_error_log(log, calling_function)
        exit(1)
    else:
        print(":white_check_mark:\tInstalled dependencies in the virtual environment")


def create_error_log(log: str, calling_function: str) -> None:
    """Creates a file with log of error in the current folder.

    Args:
        log: The content of the error log.
        calling_function: The function in which the error occured. Used to give a more descriptive name to error log file.
    """
    try:
        error_logs_path = f"{HOME_PATH}/ssb-project-cli/.error_logs"
        if not os.path.exists(error_logs_path):
            os.makedirs(error_logs_path)
        filename = f"{calling_function}-error-{int(time.time())}.txt"
        with open(f"{error_logs_path}/{filename}", "w+") as f:
            f.write(log)
            typer.echo(
                f"Detailed error information saved to {error_logs_path}/{filename}"
            )
            f.close()
    except Exception as e:
        typer.echo(f"Error while attempting to write the log file: {e}")


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


@app.command()
def clean(
    project_name: str = typer.Argument(  # noqa: B008
        ..., help="The name of the project/kernel you want to delete."
    )
) -> None:
    """Deletes the kernel corresponding to the provided project name."""
    kernels = get_kernels_dict()

    if project_name not in kernels:
        typer.echo(
            f'Could not find kernel "{project_name}". Is the project name spelled correctly?'
        )

        exit(1)

    confirmation = questionary.confirm(
        f"Are you sure you want to delete the kernel '{project_name}'. This action will delete the kernel associated with the virtual environment and leave all other files untouched."
    ).ask()

    if not confirmation:
        exit(1)

    typer.echo(
        f"Deleting kernel {project_name}...If you wish to also delete the project files, you can do so manually."
    )

    clean_cmd = f"jupyter kernelspec remove -f {project_name}".split()

    result = subprocess.run(  # noqa: S603 no untrusted input
        clean_cmd, capture_output=True
    )

    output = result.stderr.decode("utf-8").strip()

    if (
        result.returncode != 0
        or output != f"[RemoveKernelSpec] Removed {kernels[project_name]}"
    ):

        calling_function = "clean-kernel"
        log = str(result)

        typer.echo("Error: Something went wrong while removing the jupyter kernel.")
        create_error_log(log, calling_function)
        exit(1)

    print(f"Deleted Jupyter kernel {project_name}.")


def create_github(
    github_token: str, repo_name: str, repo_privacy: str, repo_description: str
) -> str:
    """Creates a GitHub repository with name, description and privacy setting.

    Args:
        github_token: GitHub personal access token
        repo_name: Repository name
        repo_privacy: Repository privacy setting, see RepoPrivacy for more information
        repo_description: Repository description

    Returns:
        str: Repository url
    """
    private_repo = True if repo_privacy != "public" else False

    g = Github(github_token)
    if not debug_without_create_repo:
        try:
            g.get_organization(GITHUB_ORG_NAME).create_repo(
                repo_name,
                private=private_repo,
                auto_init=False,
                description=repo_description,
            )
        except BadCredentialsException:
            print("Error: Invalid Github credentials")
            create_error_log(
                "".join(format_exc()),
                "create_github",
            )
            exit(1)

    repo_url = g.get_repo(f"{GITHUB_ORG_NAME}/{repo_name}").clone_url
    g.get_repo(f"{GITHUB_ORG_NAME}/{repo_name}").replace_topics(["ssb-project"])
    return repo_url


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
        typer.echo("An error occured while looking for installed kernels.")
        exit(1)
    kernel_dict = {}
    for kernel in kernels_str.split("\n")[1:]:
        line = " ".join(kernel.strip().split())
        if len(line.split(" ")) == 2:
            k, v = line.split(" ")
            kernel_dict[k] = v
    return kernel_dict


def main() -> None:
    """Main function of ssb_project_cli."""
    app(prog_name="ssb-project")  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
