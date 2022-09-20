import argparse
import logging
import sys

from git import Repo
from github import Github

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("create-github-repos.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main(token):
    logging.info("Scanning organization for active public repos...")
    g = Github(token)

    public_repos = []
    for repo in g.get_organization("statisticsnorway").get_repos(type="public"):
        if not repo.archived:
            logging.info(f"{repo.full_name} is public")
            public_repos.append(repo)
    logging.info(f"There are {len(public_repos)} public repos")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument("token", help="GitHub Personal Access Token")
    args = parser.parse_args()

    main(args.token)
