import os

try:
    """
    Use:
    * os.environ for mandatory envvars
    * os.getenv for optional envvars
    """
    LOGLEVEL = os.getenv("LOGLEVEL", default="DEBUG")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    DYNAMO_ENDPOINT = os.getenv("DYNAMO_ENDPOINT", None)
    FIXTURE_PATH = os.getenv("FIXTURE_PATH", "tests/fixture.json")
    JOB_CREATION_FUNCTION = os.getenv("JOB_CREATION_FUNCTION", None)
    JOB_CREATION_FUNCTION_ARN = os.getenv("JOB_CREATION_FUNCTION_ARN", None)
    JOB_TABLE = os.getenv("JOB_TABLE", "etl_assembly_jobs")
    USER_CONF_TABLE = os.getenv("USER_CONF_TABLE", "etl_assembly_user_configs")
    TEMPLATES_TABLE = os.getenv("TEMPLATES_TABLE", "etl_assembly_templates")
    EXTRACT_JOBS_QUEUE = os.getenv("EXTRACT_JOBS_QUEUE", None)
    HISTORY_JOBS_QUEUE = os.getenv("HISTORY_JOBS_QUEUE", None)
    TRANSFORM_JOBS_QUEUE = os.getenv("TRANSFORM_JOBS_QUEUE", None)
    LOAD_JOBS_QUEUE = os.getenv("LOAD_JOBS_QUEUE", None)
    BIG_PAYLOADS_BUCKET = os.getenv("BIG_PAYLOADS_BUCKET", None)

    HISTORY_MESSAGES_RATE = int(os.getenv("HISTORY_MESSAGES_RATE", "3"))
    TIMEWINDOW_SIZE = int(os.getenv("TIMEWINDOW_SIZE", "3"))  # in minutes
except KeyError as k:
    raise Exception(f"Missing {k} environment variable")
