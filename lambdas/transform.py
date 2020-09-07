from core import config
from core.etl import SqsQueue, Transform
from core.assembly import transformation_stage
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    serialized_job = event["body"]
    job = Transform.deserialize(serialized_job)
    load_queue = SqsQueue(queue_url=config.LOAD_JOBS_QUEUE)
    transformation_stage(job, load_queue)
