from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    # Build a job object
    logger.debug(f"Handling event {event}")
