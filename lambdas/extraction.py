from core import config
from core.etl import SqsQueue
from core.assembly import extraction_stage
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    conf_id = event["config_id"]
    transformation_queue = SqsQueue(queue_url=config.TRANSFORM_JOBS_QUEUE)
    extraction_stage(conf_id, transformation_queue)
