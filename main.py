"""
This module is for exploring the implementation of the ETL thing
"""
import argparse
from core.assembly import main

import core.config as config
from core.logs import get_logger
from core.etl import InMemoryQueue
from core.database import (
    create_tables,
    load_fixtures,
    TemplateTable,
    JobTable,
    UserConfTable,
)


def build_database():
    tables = [TemplateTable, JobTable, UserConfTable]
    logger.info("Creating tables")
    create_tables(tables)
    logger.info("Tables created")
    logger.info("Loading fixtures")
    load_fixtures(tables, config.FIXTURE_PATH)


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
        "job_id", help="Job ID to run",
    )
    args = parser.parse_args()

    logger = get_logger("main")

    if args.build_database:
        build_database()

    # Simulate message queues
    logger.info("Building queues")
    queue = InMemoryQueue()
    logger.info("Queues built")

    # Probably we want to programatically schedule executions. Check the link:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html
    # CloudWatch events scheduling

    # Build a job object
    main(args.job_id, queue)

# Maybe use TS report id as MISP event UUID?
