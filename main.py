"""
This module is for exploring the implementation of the ETL thing
"""
from logs import get_logger
from etl import Extract, Transform, Load, ExtractQueue, TransformQueue, LoadQueue
from registry import JobConfig
from database import (
    create_tables,
    load_fixtures,
    TemplateTable,
    JobConfigTable,
    UserConfTable,
)

if __name__ == "__main__":

    logger = get_logger("main")
    tables = [TemplateTable, JobConfigTable, UserConfTable]
    logger.info("Creating tables")
    create_tables(tables)
    logger.info("Tables created")

    logger.info("Loading fixtures")
    load_fixtures(tables)

    # Simulate message queues
    logger.info("Building queues")
    extract_q = ExtractQueue()
    transform_q = TransformQueue()
    load_q = LoadQueue()
    logger.info("Queues built")

    # Build a job description object
    logger.info("Retrieving job config")
    job_config = JobConfig.get(_id="7f9010e3-f1b9-408a-8fbf-85fe20f8fd34")
    logger.info("Retrieving done")

    # Build an Extract job
    # queue for extraction
    logger.info("Building an Extract job")
    job = Extract.build(job_config)
    logger.info("Queuing Extract job")
    extract_q.put(job)

    # Perform an extraction
    logger.info("Retrieving Extract job")
    extract_job = extract_q.get()
    logger.info("Running Extract job")
    extracted_data = extract_job.run()
    # attach the extracted data to the ETL job
    # queue for transformation
    logger.info("Building a Transform job")
    job = Transform.build(extract_job.job_config, extracted_data)
    logger.info("Queuing the Transform job")
    transform_q.put(job)

    # Perform a transformation
    logger.info("Retrieving a Transform job")
    transform_job = transform_q.get()
    logger.info("Running the Transform job")
    transformed_data = transform_job.run()
    # attach the transformed data to the etl job
    # queue for loading
    logger.info("Building a Load job")
    job = Load.build(transform_job.job_config, transformed_data)
    logger.info("Queuing the Load job")
    load_q.put(job)

    # Perform a load
    logger.info("Retrieving a Load job")
    load_job = load_q.get()
    logger.info("Running a load job")
    loaded_data = load_job.run()
    logger.info("That's it")
    # END
