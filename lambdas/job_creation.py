from core.assembly import job_creation_stage
from core.logs import get_logger
from core.queues import get_sqs_queues

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    queues = get_sqs_queues()
    conf_id = event["config_id"]
    job_creation_stage(conf_id, queues.extract)
