"""This module contains GitHub related functionality used when creating ssb-projects."""
import re
from pathlib import Path
from traceback import format_exc

import questionary
import requests
from github import BadCredentialsException
from github import Github
from github import GithubException

from ssb_project_cli.ssb_project import prompt_autocomplete_style
from ssb_project_cli.ssb_project.build.environment import JUPYTER_IMAGE_SPEC
from ssb_project_cli.ssb_project.build.environment import running_onprem
from ssb_project_cli.ssb_project.settings import GITHUB_ORG_NAME
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
    g = get_environment_specific_github_object(github_token)

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
        get_environment_specific_github_object(token).get_repo(
            f"{github_org_name}/{repo_name}"
        )
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
    repo = get_environment_specific_github_object(github_token).get_repo(
        f"{github_org_name}/{repo_name}"
    )
    repo.get_branch("main").edit_protection(
        required_approving_review_count=1,
        dismiss_stale_reviews=True,
        enforce_admins=True,
        user_bypass_pull_request_allowances=[],  # Supply this as workaround for https://github.com/PyGithub/PyGithub/issues/2578
    )


def get_environment_specific_github_object(github_token: str) -> Github:
    """Creates and returns a `Github` object with appropriate settings based on the environment.

    Args:
        github_token: A personal access token for authenticating with the GitHub API.

    Returns:
        A `Github` object that can be used to interact with the GitHub API.

    This function creates a `Github` object that is specific to the current environment.
    If the function is running in the onprem environment, SSL verification uses /etc/ssl/certs/ca-certificates.crt.
    Otherwise, SSL verification is enabled.
    """
    if running_onprem(JUPYTER_IMAGE_SPEC):
        # CA bundle to use, supplying this fixes the onprem error "CERTIFICATE_VERIFY_FAILED"
        # verify can be boolean or string, we have to type ignore because mypy expects it to be a bool
        return Github(github_token, verify="/etc/ssl/certs/ca-certificates.crt")
    else:
        return Github(github_token)


def get_org_members(github_token: str) -> list[str]:
    """Returns a list of login names for all members of a GitHub organization.

    Args:
        github_token: GitHub API token.

    Returns:
        list: A list of strings, where each string is the login name of a member of the organization.
    """
    # Set up the API endpoint URL and initial query parameters
    url = f"https://api.github.com/orgs/{GITHUB_ORG_NAME}/members"
    params = {"per_page": 100, "page": 1}
    headers = {"Authorization": f"Bearer {github_token}"}

    # Store usernames
    github_usernames = []

    while True:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20,
            verify="/etc/ssl/certs/ca-certificates.crt",
        )

        if response.status_code == 200:
            members = response.json()
            if len(members) == 0:
                break

            for member in members:
                github_usernames.append(member["login"])
            params["page"] += 1
        else:
            print("Error: could not retrieve member list")
            response_json, response_status = response.json(), response.status_code
            create_error_log(f"{response_json=}, {response_status=}", "get_org_members")
            exit(1)

    return github_usernames


def get_github_username(github: Github, github_token: str) -> str:
    """Get the user's GitHub username.

    If running on-prem, prompt the user to select their username from a list of
    organization members. Otherwise, retrieve the user's username from GitHub.

    Args:
        github: An instance of the `Github` class.
        github_token: GitHub API token.

    Returns:
        str: The user's GitHub username.
    """
    if running_onprem(JUPYTER_IMAGE_SPEC):
        org_members = get_org_members(github_token)
        user_value: str = questionary.autocomplete(
            message="Enter your GitHub username:",
            choices=org_members,
            style=prompt_autocomplete_style,
            validate=lambda text: text.lower()
            in [member.lower() for member in org_members],
        ).ask()
        return user_value
    else:
        return github.get_user().login
