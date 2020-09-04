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
    JOB_CREATION_FUNCTION = os.getenv("JOB_CREATION_FUNCTION", None)
    JOB_CREATION_FUNCTION_ARN = os.getenv("JOB_CREATION_FUNCTION_ARN", None)
    EXTRACTION_JOB_QUEUE = os.getenv("EXTRACTION_JOB_QUEUE", None)
    JOB_TABLE = os.getenv("JOB_TABLE", None)
    USER_CONF_TABLE = os.getenv("USER_CONF_TABLE", None)
    TEMPLATES_TABLE = os.getenv("TEMPLATES_TABLE", None)
except KeyError as k:
    raise Exception(f"Missing {k} environment variable")
