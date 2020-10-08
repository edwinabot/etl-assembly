from core import config
from core.etl import Extract, SqsQueue
from core.assembly import job_creation_stage
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    conf_id = event["config_id"]
    extraction_queue = SqsQueue(queue_url=config.EXTRACT_JOBS_QUEUE, job_type=Extract)
    job_creation_stage(conf_id, extraction_queue)
