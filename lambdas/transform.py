from core import config
from core.etl import Load, SqsQueue, Transform
from core.assembly import transformation_stage
from core.logs import get_logger
from core.queues import get_sqs_queues

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    queues = get_sqs_queues()
    for record in event["Records"]:
        serialized_job = record["body"]
        job = Transform.deserialize(serialized_job)
        transformation_stage(job, queues.load)
        queues.transform.delete_message(record['receiptHandle'])
