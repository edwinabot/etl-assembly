"""
This module is for exploring the implementation of the ETL thing
"""
import argparse

from datetime import datetime, timezone

import config
from logs import get_logger
from etl import Extract, Transform, Load, ExtractQueue, TransformQueue, LoadQueue
from registry import Job

from database import (
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
    extract_q = ExtractQueue()
    transform_q = TransformQueue()
    load_q = LoadQueue()
    logger.info("Queues built")

    # Probably we want to programatically schedule executions. Check the link:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html
    # CloudWatch events scheduling

    # Build a job object
    logger.info("Retrieving job config")
    base_job = Job.get(_id=args.job_id)  # trustar misp

    logger.info("Retrieving done")

    # Build an Extract job
    # queue for extraction
    logger.info("Building an Extract job")
    extract_job = Extract.build(base_job)
    logger.info("Queuing Extract job")
    extract_q.put(extract_job)

    # Perform an extraction
    logger.info("Retrieving Extract job")
    extract_job = extract_q.get()
    logger.info("Running Extract job")
    current_run_datetime = datetime.now(timezone.utc)
    extracted_data = extract_job.run()
    extract_job.update_extraction_datetime(current_run_datetime)
    if not extracted_data:
        logger.info(
            f"No new data for job {extract_job.job.name} - ID {extract_job.job.id}"
        )
        exit(0)

    # attach the extracted data to the ETL job
    # queue for transformation
    logger.info("Building a Transform job")
    transform_job = Transform.build(extract_job.job, extracted_data)
    logger.info("Queuing the Transform job")
    transform_q.put(transform_job)

    # Perform a transformation
    logger.info("Retrieving a Transform job")
    transform_job = transform_q.get()
    logger.info("Running the Transform job")
    transformed_data = transform_job.run()
    # attach the transformed data to the etl job
    # queue for loading
    logger.info("Building a Load job")
    load_job = Load.build(transform_job.job, transformed_data)
    logger.info("Queuing the Load job")
    load_q.put(load_job)

    # Perform a load
    logger.info("Retrieving a Load job")
    load_job = load_q.get()
    logger.info("Running a load job")
    loaded_data = load_job.run()
    logger.info("That's it")
    # END

# Maybe use TS report id as MISP event UUID?
