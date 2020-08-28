from core.assembly import retrieve_job
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    # Build a job object
    logger.debug(f"Handling event {event}")
    job = retrieve_job(event["job_id"])
