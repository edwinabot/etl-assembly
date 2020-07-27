import os

try:
    """
    Use:
    * os.environ for mandatory envvars
    * os.getenv for optional envvars
    """
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    DYNAMO_ENDPOINT = os.getenv("DYNAMO_ENDPOINT", None)
    FIXTURE_PATH = os.getenv("FIXTURE_PATH", "tests/fixture.json")
except KeyError as k:
    raise Exception(f"Missing {k} environment variable")
