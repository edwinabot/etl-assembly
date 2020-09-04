from core import config
from core.etl import SqsQueue
from core.assembly import job_creation_stage
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    # Build a job object
    logger.debug(event)
    logger.debug(context)
    # {'config_id': '6c7e83fd-9c22-45ff-829d-59c887917c6f'}
    conf_id = event["config_id"]
    transformation_queue = SqsQueue(queue_url=config.EXTRACT_JOBS_QUEUE)
    job_creation_stage(conf_id, transformation_queue)
