#!/usr/bin/python3
"""Command-line-interface for project-operations in dapla-jupterlab."""
import json
import re
import subprocess  # noqa: S404
from enum import Enum
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
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


# Don't print with color, it's difficult to read when run in Jupyter
console = Console(color_system=None)
print = console.print

app = typer.Typer(
    help="Usage instructions: https://statisticsnorway.github.io/dapla-manual/ssb-project.html",
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,  # Locals can contain sensitive information
)
GITHUB_ORG_NAME = "statisticsnorway"
debug_without_create_repo = False
DEFAULT_REPO_CREATE_PATH = Path.home()
CURRENT_WORKING_DIRECTORY = Path.cwd()


def is_github_repo(token: str, repo_name: str) -> bool:
    """Checks if a Repository already exists in the organization.

    Args:
        repo_name:  Repository name
        token: GitHub personal access token.

    Returns:
        True if the repository exists, else false.

    Raises:
        ValueError: when supplied with bad GitHub credentials.
    """
    try:
        Github(token).get_repo(f"{GITHUB_ORG_NAME}/{repo_name}")
    except BadCredentialsException as ex:
        raise ValueError("Invalid Github credentials") from ex
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
    description: str = typer.prompt("Project description:")

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
    projectname: str, description: str, temp_dir: Path
) -> Path:
    """Creates a project from CookiCutter template.

    Args:
        projectname: Name of project
        description: Project description
        temp_dir: Temporary directory path

    Returns:
        Path: Path of project.

    Raises:
        ValueError: If the project directory already exists
    """
    home_dir = DEFAULT_REPO_CREATE_PATH
    project_dir = home_dir.joinpath(projectname)
    if project_dir.exists():
        raise ValueError(f"Folder '{project_dir}' already exists.")

    name, email = extract_name_email()
    if not (name and email):
        name, email = request_name_email()

    template_info = {
        "project_name": projectname,
        "description": description,
        "full_name": name,
        "email": email,
    }
    quoted = json.dumps(template_info).replace('"', '"')

    argv = [
        "cruft",
        "create",
        "https://github.com/statisticsnorway/stat-hurtigstart-template-master",
        "--no-input",
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
    """:sparkles: Create a project locally, and optionally on Github with the flag --github. The project will follow SSB's best practice for development."""
    if not valid_repo_name(project_name):
        raise ValueError(
            "Invalid repo name, please choose a name in the form 'my-fantastic-project'"
        )

    if add_github and not github_token:
        github_token = choose_login()

    if add_github and not github_token:
        raise ValueError(
            "Github token needed, please supply it with '--github-token xxxx'"
        )

    if not debug_without_create_repo:
        if add_github and is_github_repo(github_token, project_name):
            raise ValueError(f"A repo called {project_name} already exists on GitHub.")

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

            print(f":white_check_mark: Created Github repo. View it here: {repo_url}")
        else:
            make_and_init_git_repo(git_repo_dir)

        project_directory = CURRENT_WORKING_DIRECTORY / project_name
        temp_project_directory = Path(temp_dir) / project_name

        print(
            f":white_check_mark: Created project ({project_name}) in the folder {project_directory}"
        )

        build(path=str(temp_project_directory))

        copytree(temp_project_directory, project_directory)

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
    """:wrench: Create a virtual environment and corresponding Jupyter kernel. Runs in the current folder if no arguments are supplied."""
    project_directory = Path(path)

    project_name = CURRENT_WORKING_DIRECTORY.name

    if path == "":
        project_name = CURRENT_WORKING_DIRECTORY.name
        project_directory = CURRENT_WORKING_DIRECTORY
    else:
        project_name = project_directory.name

    poetry_install(project_directory)

    install_ipykernel(project_directory, project_name)


def get_github_pat() -> dict[str, str]:
    """Gets GitHub users and PAT from .gitconfig.

    Raises:
        ValueError: If .git-credentials does not exist.

    Returns:
        dict[str, str]: A dict with user as key and PAT as value.
    """
    git_credentials = DEFAULT_REPO_CREATE_PATH.joinpath(Path(".git-credentials"))
    user_token_dict: dict[str, str] = {}
    if not git_credentials.exists():
        raise ValueError(
            "Couldn't find .git-credentials, supply your Github token with '--github-token xxxx'"
        )

    with open(git_credentials) as f:
        lines = f.readlines()

        for line in lines:
            user_token_split = line.split(":")
            user = re.sub(r".*//", "", user_token_split[1])
            token = re.sub(r"@.*", "", user_token_split[2]).strip()
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

    Returns:
        str: GitHub personal access token
    """
    user_token_dict: dict[str, str] = get_github_pat()

    choice = questionary.select(
        "Select your GitHub account:", choices=user_token_dict.keys()  # type: ignore
    ).ask()

    return user_token_dict[choice]


def install_ipykernel(project_directory: Path, project_name: str) -> None:
    """Installs ipykernel.

    Args:
        project_directory: Path of project
        project_name: Name of project

    Raises:
        ValueError: If the process returns with error code
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
            raise ValueError(
                f'Error during installation of the Jupyter kernel: {result.stderr.decode("utf-8")}'
            )

    print(f":white_check_mark: Installed Jupyter Kernel ({project_name})")


def poetry_install(project_directory: Path) -> None:
    """Call poetry install in project_directory.

    Args:
        project_directory: Path of project

    Raises:
        ValueError: If the process returns with error code
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Installing dependencies...", total=None)
        result = subprocess.run(  # noqa: S603 no untrusted input
            "poetry install".split(), capture_output=True, cwd=project_directory
        )
    if result.returncode != 0:
        raise ValueError(
            f'Error during installation of dependencies: {result.stderr.decode("utf-8")}'
        )
    else:
        print(":white_check_mark: Installed dependencies in the virtual environment")


@app.command()
def clean(
    project_name: str = typer.Argument(  # noqa: B008
        ..., help="Name of the kernel to be deleted"
    )
) -> None:
    """:broom: Delete the project's Jupyter kernel."""
    kernels = get_kernels_dict()

    if project_name not in kernels:
        raise ValueError(
            f'Could not find Jupyter kernel "{project_name}". Is the name correct?'
        )

    print(f"Deleting Jupyter kernel {project_name}...")

    clean_cmd = f"jupyter kernelspec remove -f {project_name}".split()

    result = subprocess.run(  # noqa: S603 no untrusted input
        clean_cmd, capture_output=True
    )

    if result.returncode != 0:
        raise ValueError(
            f'Error while deleting the Jupyter kernel: {result.stderr.decode("utf-8")}'
        )

    output = result.stderr.decode("utf-8").strip()
    if output != f"[RemoveKernelSpec] Removed {kernels[project_name]}":
        raise ValueError(
            f'Error while deleting the Jupyter kernel: {result.stderr.decode("utf-8")}'
        )

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
        g.get_organization(GITHUB_ORG_NAME).create_repo(
            repo_name,
            private=private_repo,
            auto_init=False,
            description=repo_description,
        )
    repo_url = g.get_repo(f"{GITHUB_ORG_NAME}/{repo_name}").clone_url
    g.get_repo(f"{GITHUB_ORG_NAME}/{repo_name}").replace_topics(["ssb-project"])
    return repo_url


def get_kernels_dict() -> dict[str, str]:
    """Makes a dictionary of installed kernel specifications.

    Raises:
        ValueError: If the jupyter subprocess does not return 0

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
        raise ValueError(kernels_process.stderr.decode("utf-8"))
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
