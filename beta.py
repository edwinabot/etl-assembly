"""
This module is for exploring the implementation of the ETL thing
"""
import argparse
import queue
from core.registry import Job
from queue import Empty
from datetime import datetime, timezone, timedelta

from core.logs import get_logger
from core.etl import Extract, Transform, Load, HistoricalIngestHandler, HistoryExtract
from core.queues import get_in_memory_queues
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
        "job_id",
        help="Job ID to run",
    )
    args = parser.parse_args()

    logger = get_logger("main")

    if args.build_database:
        build_database()

    # Simulate message queues
    logger.info("Building queues")

    # Probably we want to programatically schedule executions. Check the link:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html
    # CloudWatch events scheduling

    queues = get_in_memory_queues()

    job_creation_stage(args.job_id, queues.extract)
    """
    # job_creation_stage(args.job_id, queues.extract)
    job = Job.get(args.job_id)
    to = datetime(2020, 10, 27, 18, 0, 0, 0, timezone.utc)
    hist_job = Extract(job, {"from": to - timedelta(hours=2), "to": to})
    queues.history.put([hist_job])
    keep_going = True
    """
    keep_going = True
    while keep_going:
        try:
            logger.debug("Retrieving Extract job")
            extract_job = queues.extract.get()
            extraction_stage(extract_job, queues.transform)
        except Empty:
            logger.debug("No more stuff to Extract")
            keep_going = False

    keep_going = True
    while keep_going:
        try:
            logger.debug("Retrieving Transform job")
            transform_job = queues.transform.get()  # type: Transform
            transformation_stage(transform_job, queues.load)
        except Empty:
            logger.debug("No more stuff to Transform")
            keep_going = False

    keep_going = True
    while keep_going:
        try:
            logger.debug("Retrieving Load job")
            load_job = queues.load.get()  # type: Load
            loading_stage(load_job)
        except Empty:
            logger.debug("No more stuff to Load")
            keep_going = False
