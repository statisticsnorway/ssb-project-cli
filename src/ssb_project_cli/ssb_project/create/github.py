"""This module contains GitHub related functionality used when creating ssb-projects."""
import re
from pathlib import Path
from traceback import format_exc

from github import BadCredentialsException
from github import Github
from github import GithubException

from ssb_project_cli.ssb_project.util import create_error_log


def create_github(
    github_token: str,
    repo_name: str,
    repo_privacy: str,
    repo_description: str,
    github_org_name: str,
) -> str:
    """Creates a GitHub repository with name, description and privacy setting.

    Args:
        github_token: GitHub personal access token
        repo_name: Repository name
        repo_privacy: Repository privacy setting, see RepoPrivacy for more information
        repo_description: Repository description
        github_org_name: Name of GitHub organization

    Returns:
        str: Repository url
    """
    g = Github(github_token)

    try:
        # Ignoring mypy warning: Unexpected keyword argument "visibility"
        # for "create_repo" of "Organization"  [call-arg]
        g.get_organization(github_org_name).create_repo(  # type: ignore
            repo_name,
            visibility=repo_privacy,
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

    repo = g.get_repo(f"{github_org_name}/{repo_name}")
    repo.replace_topics(["ssb-project"])

    return repo.clone_url


def get_github_pat(path: Path) -> dict[str, str]:
    """Gets GitHub users and PAT from .gitconfig and .netrc.

    Args:
        path: Path to folder containing GitHub credentials.

    Returns:
        dict[str, str]: A dict with user as key and PAT as value.
    """
    user_token_dict = get_github_pat_from_gitcredentials(
        path
    ) | get_github_pat_from_netrc(path)

    if not user_token_dict:
        print(
            "Could not find your github token. Add it manually with the --github-token <TOKEN> option\n or fix it by following this guide: https://manual.dapla.ssb.no/git-github.html#sec-pat"
        )
        exit(1)
    return user_token_dict


def get_github_pat_from_gitcredentials(credentials_path: Path) -> dict[str, str]:
    """Gets GitHub users and PAT from .gitconfig.

    Args:
        credentials_path: Path to folder containing .git-credentials

    Returns:
        dict[str, str]: A dict with user as key and PAT as value.
    """
    git_credentials_file = credentials_path.joinpath(Path(".git-credentials"))
    user_token_dict: dict[str, str] = {}

    if not git_credentials_file.exists():
        return user_token_dict

    with open(git_credentials_file) as f:
        lines = f.readlines()
        for line in lines:
            p = re.compile("https://([A-Za-z0-9_-]+):([A-Za-z0-9_]+)@github.com")
            res = p.match(line)

            if res:
                user = res.group(1)
                token = res.group(2)
                user_token_dict[user] = token

    return user_token_dict


def get_github_pat_from_netrc(netrc_path: Path) -> dict[str, str]:
    """Gets GitHub users and PAT from .netrc.

    Args:
        netrc_path: Path to folder containing .netrc

    Returns:
        dict[str, str]: A dict with user as key and PAT as value.
    """
    credentials_netrc_file = netrc_path.joinpath(Path(".netrc"))
    user_token_dict: dict[str, str] = {}

    if not credentials_netrc_file.exists():
        return user_token_dict

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


def is_github_repo(token: str, repo_name: str, github_org_name: str) -> bool:
    """Checks if a Repository already exists in the organization.

    Args:
        repo_name:  Repository name
        token: GitHub personal access token
        github_org_name: Name of GitHub organization

    Returns:
        True if the repository exists, else false.
    """
    try:
        Github(token).get_repo(f"{github_org_name}/{repo_name}")
    except ValueError:
        print(
            "The provided Github credentials are invalid. Please check that your personal access token is not expired."
        )
        exit(1)
    except GithubException:
        return False
    else:
        return True


def set_branch_protection_rules(
    github_token: str, repo_name: str, github_org_name: str
) -> None:
    """Sets branch default protection rules.

    The following rules are set:
    Main branch pull requests requires a minimum of 1 reviewer.
    Reviews that are no longer valid can be dismissed.
    When you dismiss a review, you must add a comment explaining why you dismissed it.

    Args:
        github_token: GitHub personal access token
        repo_name: name of repository
        github_org_name: Name of GitHub organization
    """
    repo = Github(github_token).get_repo(f"{github_org_name}/{repo_name}")
    repo.get_branch("main").edit_protection(
        required_approving_review_count=1, dismiss_stale_reviews=True
    )
