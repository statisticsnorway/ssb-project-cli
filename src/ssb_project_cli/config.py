
import os


ENVIRONMENT = "PROD" if "prod" in os.environ["CLUSTER_ID"] else "STAGING"
PIP_INDEX_URL = os.environ["PIP_INDEX_URL"]

