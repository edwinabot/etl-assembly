from core.etl import Load
from core.assembly import loading_stage
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    for record in event["Records"]:
        serialized_job = record["body"]
        job = Load.deserialize(serialized_job)
        loading_stage(job)
