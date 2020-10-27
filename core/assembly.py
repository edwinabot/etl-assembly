from datetime import datetime, timezone
from typing import Any, Union

from core.etl import (
    AbstractQueue,
    InMemoryQueue,
    SqsQueue,
    Extract,
    Transform,
    Load,
    Job,
)
from core.logs import get_logger

logger = get_logger(__name__)


def main(job_id, queue: Union[InMemoryQueue, SqsQueue]) -> None:
    """
    A main function usefull for local development and integration testing
    """
    job_creation_stage(job_id, queue)

    logger.debug("Retrieving Extract job")
    extract_job = queue.get()  # type: Extract
    extraction_stage(extract_job, queue)

    logger.debug("Retrieving Transform job")
    transform_job = queue.get()  # type: Transform
    transformation_stage(transform_job, queue)

    logger.debug("Retrieving Load job")
    load_job = queue.get()  # type: Load
    loading_stage(load_job)


def job_creation_stage(config_id: str, queue: AbstractQueue) -> None:
    extract_job = create_extraction_job(config_id)
    queue.put([extract_job])


def extraction_stage(extract_job: Extract, queue: AbstractQueue, is_historical=False):
    # Perform an extraction
    logger.debug(f"Starting extraction stage job {extract_job.job.id}")
    current_run_datetime = datetime.now(timezone.utc)
    extracted_data = run_extraction_job(extract_job)
    if not extracted_data:
        logger.info(
            f"Job ID {extract_job.job.id} ({extract_job.job.name}): no new data"
        )
    else:
        transform_jobs = create_transformation_job(extract_job, extracted_data)
        queue.put(transform_jobs)
    if not is_historical:
        extract_job.update_extraction_datetime(current_run_datetime)


def transformation_stage(transform_job: Transform, queue: AbstractQueue) -> None:
    logger.debug(f"Starting transformation job {transform_job.job.id}")
    # Perform a transformation
    transformed_data = run_transformation_job(transform_job)
    if not transformed_data:
        logger.info(
            f"Job ID {transform_job.job.id} "
            f"({transform_job.job.name}): no data to transform"
        )
    else:
        load_jobs = create_loading_job(transform_job, transformed_data)
        queue.put(load_jobs)


def loading_stage(load_job: Load) -> None:
    logger.debug(f"Starting loading job {load_job.job.id}")
    run_loading_job(load_job)


def create_extraction_job(config_id: str) -> Extract:
    """
    Creates an Extract job out of a Job ID

    Params:
    =======

    :config_id: str: Job ID to be used for creating the Extract job
    """
    # Build a job object
    logger.debug(f"Retrieving job config {config_id}")
    base_job = Job.get(_id=config_id)

    # Build an Extract job
    # queue for extraction
    logger.debug(f"Building an Extract job using config {config_id}")
    extract_job = Extract.build(base_job)
    return extract_job


def run_extraction_job(extract_job: Extract) -> Any:
    logger.info(f"Running Extract job {extract_job.job.id}")
    extracted_data = extract_job.run()
    return extracted_data


def create_transformation_job(extract_job: Extract, extracted_data: list) -> list:
    """
    Creates a Transform job following and Extract job for the extracted data

    Params:
    =======

    :extract_job: Extract: The extract job after which to create the tramsform job
    :extracted_data: Any: The data to be transformed
    :partition_size: int: Data partition size in bytes
    """
    jobs = []
    logger.info(f"Building a Transform job {extract_job.job.id}")
    transform_job = Transform.build(extract_job.job, extracted_data)
    jobs.append(transform_job)
    return jobs


def run_transformation_job(transform_job: Transform) -> Any:
    logger.debug(f"Running Transform job {transform_job.job.id}")
    transformed_data = transform_job.run()
    return transformed_data


def create_loading_job(transform_job: Transform, transformed_data: Any) -> list:
    jobs = []
    logger.info(f"Building a Load job {transform_job.job.id}")
    load_job = Load.build(transform_job.job, transformed_data)
    jobs.append(load_job)
    return jobs


def run_loading_job(load_job: Load) -> Any:
    logger.debug(f"Running a Load job {load_job.job.id}")
    loaded_data = load_job.run()
    return loaded_data
