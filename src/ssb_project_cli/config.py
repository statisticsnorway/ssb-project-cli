
import os


ENVIRONMENT = "PROD" if "prod" in os.environ["CLUSTER_ID"] else "STAGING"