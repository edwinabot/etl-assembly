"""
This module is for exploring the implementation of the ETL thing
"""
import argparse
from queue import Empty

from core.logs import get_logger
from core.etl import (
    InMemoryQueue,
    Extract,
    Transform,
    Load,
)
from core.assembly import (
    extraction_stage,
    transformation_stage,
    loading_stage,
    job_creation_stage,
)
from main import build_database


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
    logger.info("Queues built")

    # Probably we want to programatically schedule executions. Check the link:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html
    # CloudWatch events scheduling

    # Build a job object

    """
    A main function usefull for local development and integration testing
    """

    extract_jobs = InMemoryQueue(job_type=Extract)
    transform_jobs = InMemoryQueue(job_type=Transform)
    load_jobs = InMemoryQueue(job_type=Load)

    job_creation_stage(args.job_id, extract_jobs)

    keep_going = True
    while keep_going:
        try:
            logger.debug("Retrieving Extract job")
            extract_job = extract_jobs.get()  # type: Extract
            extraction_stage(extract_job, transform_jobs)
        except Empty:
            logger.debug("No more stuff to Extract")
            keep_going = False

    keep_going = True
    while keep_going:
        try:
            logger.debug("Retrieving Transform job")
            transform_job = transform_jobs.get()  # type: Transform
            transformation_stage(transform_job, load_jobs)
        except Empty:
            logger.debug("No more stuff to Transform")
            keep_going = False

    keep_going = True
    while keep_going:
        try:
            logger.debug("Retrieving Load job")
            load_job = load_jobs.get()  # type: Load
            loading_stage(load_job)
        except Empty:
            logger.debug("No more stuff to Load")
            keep_going = False
