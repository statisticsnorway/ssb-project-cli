#!/usr/bin/python3
"""Command-line-interface for project-operations in dapla-jupterlab."""
import json
import os
import subprocess  # noqa: S404
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import Optional
from typing import Type

import toml
import typer
from git import Repo  # type: ignore[attr-defined]
from github import BadCredentialsException
from github import Github
from github import GithubException
from rich import print
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn


app = typer.Typer(rich_markup_mode="rich")
GITHUB_ORG_NAME = "statisticsnorway"
debug_without_create_repo = False
DEFAULT_REPO_CREATE_PATH = Path.home()


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
        raise ValueError("Bad GitHub Credentials.") from ex
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
        """Deletes remote self.origen and creates a remote named origen with an url."""
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
    print(f"Repo successfully pushed to GitHub: {github_url}")


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
    email = typer.prompt("Enter email    : ")
    return name, email


def request_project_description() -> str:
    """Prompts the user for a project description.

    Continues to prompt the user until a non-empty string is supplied.

    Returns:
         str: Project description
    """
    description: str = typer.prompt("Fyll inn prosjektbeskrivelse")

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


def create_project_from_template(projectname: str, description: str) -> Path:
    """Creates a project from CookiCutter template.

    Args:
        projectname: Name of project
        description: Project description

    Returns:
        Path: Path of project.

    Raises:
        ValueError: If the project directory already exists
    """
    home_dir = DEFAULT_REPO_CREATE_PATH
    project_dir = home_dir.joinpath(projectname)
    if project_dir.exists():
        raise ValueError(f"The directory {project_dir} already exists.")

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

    subprocess.run(argv, check=True, cwd=home_dir)  # noqa: S603 no untrusted input

    return project_dir


class RepoPrivacy(str, Enum):
    """Class with predefined privacy enums."""

    internal = "internal"
    private = "private"
    public = "public"


@app.command()
def create(
    project_name: str = typer.Argument(  # noqa: B008
        ..., help="Prosjekt navn, kun alfanumerisk og underscore"
    ),
    description: str = typer.Argument(  # noqa: B008
        "", help="En kort beskrivelse av prosjektet ditt"
    ),
    repo_privacy: RepoPrivacy = typer.Argument(  # noqa: B008
        RepoPrivacy.internal, help="Tilgangsvalg for repoet."
    ),
    add_github: bool = typer.Option(  # noqa: B008
        False,
        "--github",
        help="Legg denne til hvis man ønsker å opprette et Github repo",
    ),
    github_token: str = typer.Option(  # noqa: B008
        "",
        help="Ditt Github PAT, følg [link=https://statistics-norway.atlassian.net/wiki/spaces/DAPLA/pages/1917779969/Oppstart+personlig+GitHub-bruker+personlig+kode+og+integrere+Jupyter+med+GitHub#Opprette-personlig-aksesskode-i-GitHub]instruksjonene her[/link] for å skape en",
    ),
) -> None:
    """:sparkles: Skap et prosjekt lokalt og på Github (hvis ønsket).Følger kjent beste praksis i SSB. :sparkles:."""
    if " " in project_name:
        raise ValueError("Spaces not allowed in projectname, use underscore?")

    if add_github and not github_token:
        raise ValueError("Needs GitHub token, please specify with --github-token")

    if not debug_without_create_repo:
        if add_github and is_github_repo(github_token, project_name):
            raise ValueError(f"The repo {project_name} already exists on GitHub.")

    if add_github and description == "":
        description = request_project_description()

    create_project_from_template(project_name, description)

    git_repo_dir = DEFAULT_REPO_CREATE_PATH.joinpath(project_name)
    if add_github:
        print("Initialise empty repo on Github")
        repo_url = create_github(github_token, project_name, repo_privacy, description)

        print("Create local repo and push to Github")
        make_git_repo_and_push(github_token, repo_url, git_repo_dir)

        print("Set branch protection rules.")
        set_branch_protection_rules(github_token, project_name)
    else:
        make_and_init_git_repo(git_repo_dir)

    print(
        f"Project {project_name} created in folder {DEFAULT_REPO_CREATE_PATH},"
        + " you may move it if you want to."
    )

    curr_path = project_name
    project_directory = DEFAULT_REPO_CREATE_PATH / curr_path

    poetry_install(project_directory)

    install_ipykernel(project_directory, project_name)


@app.command()
def build(kernel: str = "python3", curr_path: str = "") -> None:
    """Build ssb-project.

    1. Check if Cruft recommends updating?
    2. Create Venv from Poetry
    3. Create kernel from venv
    4. Create workspace?
    5. Provide link to workspace?
    """
    project_directory = DEFAULT_REPO_CREATE_PATH / curr_path

    project_name = curr_path

    poetry_install(project_directory)

    install_ipykernel(project_directory, project_name)


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
        progress.add_task(description=f"Creating kernel {project_name}...", total=None)
        make_kernel_cmd = "poetry run python3 -m ipykernel install --user --name".split(
            " "
        ) + [project_name]
        result = subprocess.run(  # noqa: S603 no untrusted input
            make_kernel_cmd, capture_output=True, cwd=project_directory
        )
        if result.returncode != 0:
            raise ValueError(
                f'Returncode of {" ".join(make_kernel_cmd)}: {result.returncode}'
                + f'\n{result.stderr.decode("utf-8")}'
            )
        output = result.stdout.decode("utf-8")
        print(output)

    print(f"Kernel ({project_name}) successfully created")


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
            f"Returncode of poetry install: {result.returncode}\n"
            + f'{result.stderr.decode("utf-8")}'
        )


# Function is deemed too complex, should probably be split up.
def delete() -> None:  # noqa C901
    """Delete project.

    1. Remove kernel
    2. Remove venv / uninstall with poetry
    3. Remove workspace, if exists?
    """
    project_name = projectname_from_currfolder(os.getcwd())
    typer.echo("Remove kernel")
    kernels_path = "/home/jovyan/.local/share/jupyter/kernels/"
    for kernel in os.listdir(kernels_path):
        if kernel.startswith(project_name):
            os.remove(kernels_path + project_name)

    typer.echo("Remove venv / uninstall with poetry")

    venvs = subprocess.run(["poetry", "env", "list"], capture_output=True)  # noqa S607
    if venvs.returncode != 0:
        raise ValueError(venvs.stderr.decode("utf-8"))
    # check
    venvs_str: str = venvs.stdout.decode("utf-8")

    delete_cmds = []
    for venv in venvs_str.split("\n"):
        if venv:
            print(venv)
            if (venv.replace("-", "").replace("_", "")).startswith(
                project_name.replace("-", "").replace("_", "")
            ):
                delete_cmds += [["poetry", "env", "remove", venv.split(" ")[0]]]

    for cmd in delete_cmds:
        deletion = subprocess.run(  # noqa: S603 no untrusted input
            cmd, capture_output=True
        )
        if deletion.returncode != 0:
            raise ValueError(deletion.stderr.decode("utf-8"))
        # typer.echo?
        print(deletion.stdout.decode("utf-8"))

    typer.echo("Remove workspace, if it exist, based on project-name")
    for workspace in os.listdir("/home/jovyan/.jupyter/lab/workspaces/"):

        if rm_hyphen_and_underscore(workspace).startswith(
            rm_hyphen_and_underscore(project_name)
        ):
            os.remove(f"/home/jovyan/.jupyter/lab/workspaces/{workspace}")


def rm_hyphen_and_underscore(s: str) -> str:
    """Remove hyphens and underscores.

    Args:
        s: input string

    Returns:
        str: without a hyphen and underscore
    """
    return s.replace("-", "").replace("_", "")


def workspace() -> None:
    """Prints uri used to create/clone a workspace."""
    typer.echo(workspace_uri_from_projectname(projectname_from_currfolder(os.getcwd())))
    typer.echo("To create/clone the workspace:")
    typer.echo(
        workspace_uri_from_projectname(projectname_from_currfolder(os.getcwd()))
        + "?clone"
    )


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
    typer.echo(f"GitHub repo created: {repo_url}")
    return repo_url


def projectname_from_currfolder(curr_path: str) -> str:
    """Retrives project name from poetry's toml-config in cwd.

    Args:
        curr_path: Optional string of current path.

    Returns:
        str: Project name from poetry`s toml-config
    """
    curr_dir = os.getcwd()
    while "pyproject.toml" not in os.listdir():
        os.chdir("../")
    pyproject = toml.load("./pyproject.toml")
    name: str = pyproject["tool"]["poetry"]["name"]
    os.chdir(curr_dir)
    return name


def workspace_uri_from_projectname(project_name: str) -> str:
    """Generates workspace uri based on project name.

    Args:
         project_name: Project name

    Returns:
        str: Workspace uri
    """
    return (
        "https://jupyter.dapla.ssb.no/user/"
        + f"{os.environ['JUPYTERHUB_USER']}/lab/workspaces/{project_name}"
    )


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
    app(prog_name="ssb-project")


if __name__ == "__main__":
    main()
