from core import config
from core.etl import SqsQueue, Extract
from core.assembly import extraction_stage
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    transformation_queue = SqsQueue(queue_url=config.TRANSFORM_JOBS_QUEUE)
    for record in event["Records"]:
        serialized_job = record["body"]
        job = Extract.deserialize(serialized_job)
        extraction_stage(job, transformation_queue)
