import argparse
from lambdas.job_creation import lambda_handler as job_creation_lambda
from lambdas.extraction import lambda_handler as extraction_lambda
from lambdas.transform import lambda_handler as transform_lambda
from lambdas.load import lambda_handler as load_lambda
from core.logs import get_logger
from core.queues import get_sqs_queues
from main import build_database


def main(args):
    queues = get_sqs_queues()

    job_creation_lambda({"config_id": args.job_id}, {})

    message = queues.extract.get_raw()
    extraction_event = mock_event(message)
    extraction_lambda(extraction_event, {})

    message = queues.transform.get_raw()
    transformation_event = mock_event(message)
    transform_lambda(transformation_event, {})

    message = queues.load.get_raw()
    load_event = mock_event(message)
    load_lambda(load_event, {})


def mock_event(message):
    return {
        "Records": [
            {
                "body": message["Messages"][0]["Body"],
                "receiptHandle": message["Messages"][0]["ReceiptHandle"],
                "messageId": message["Messages"][0]["MessageId"],
                "messageAttributes": message["Messages"][0]["MessageAttributes"],
                "md5OfBody": message["Messages"][0]["MD5OfBody"],
            }
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b",
        "-build-database",
        required=False,
        action="store_true",
        dest="build_database",
        default=False,
        help="(OPTIONAL) Recreate the database an load the fixture",
    ),
    parser.add_argument(
        "job_id",
        help="Job ID to run",
    )
    args = parser.parse_args()

    logger = get_logger("main")

    if args.build_database:
        build_database()

    main(args)
