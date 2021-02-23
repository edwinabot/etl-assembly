from core.etl import Load
from core.assembly import loading_stage
from core.logs import get_logger
from core.queues import get_sqs_queues

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    queues = get_sqs_queues()
    for record in event["Records"]:
        try:
            serialized_job = record["body"]
            job: Load = queues.load.build_job(serialized_job)
            loading_stage(job)
            queues.load.delete_message(record["receiptHandle"])
        except Exception as e:
            logger.error(record)
            logger.exception(e)
