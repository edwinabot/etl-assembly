import os

from botocore.exceptions import ConfigNotFound

try:
    AWS_REGION = os.environ["AWS_REGION"]
    DYNAMO_ENDPOINT = os.environ["DYNAMO_ENDPOINT"]
except KeyError as k:
    raise ConfigNotFound(f"Missing {k} environment variable")
