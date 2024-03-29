from queue import Empty
from core.etl import HistoryExtract
from core.assembly import extraction_stage
from core.logs import get_logger
from core.queues import get_sqs_queues
from core.config import HISTORY_MESSAGES_RATE

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    queues = get_sqs_queues()
    for _ in range(HISTORY_MESSAGES_RATE):
        try:
            job: HistoryExtract = queues.history.get()
            logger.debug(f"Job ID: {job.job.id} - window {job.window}")
            extraction_stage(job, queues.transform, is_historical=True)
        except Empty:
            logger.info("No Historical data to ingest")
            break
        except Exception as e:
            logger.error(e)
