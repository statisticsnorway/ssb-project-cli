"""Global settings for SSB-project-cli."""
import os
from pathlib import Path


GITHUB_ORG_NAME = "statisticsnorway"
HOME_PATH = Path.home()
CURRENT_WORKING_DIRECTORY = Path.cwd()
STAT_TEMPLATE_REPO_URL = "https://github.com/statisticsnorway/ssb-project-template-stat"
STAT_TEMPLATE_DEFAULT_REFERENCE = os.environ.get(
    "STAT_TEMPLATE_DEFAULT_REFERENCE", "1.0.0"
)
