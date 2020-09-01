from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    # Build a job object
    logger.error(f"Handling event {event}")
    print(event)
    print(context)
