from dataclasses import dataclass
from core import config
from core.etl import (
    HistoryExtract,
    InMemoryQueue,
    Extract,
    SqsQueue,
    Transform,
    Load,
)


@dataclass
class SqsQueues:
    extract: SqsQueue
    transform: SqsQueue
    load: SqsQueue
    history: SqsQueue


@dataclass
class InMemoryQueues:
    extract: InMemoryQueue
    transform: InMemoryQueue
    load: InMemoryQueue
    history: InMemoryQueue


def get_sqs_queues():
    extract_jobs = SqsQueue(
        queue_url=config.EXTRACT_JOBS_QUEUE,
        job_type=Extract,
        large_payload_bucket=config.BIG_PAYLOADS_BUCKET,
    )
    transform_jobs = SqsQueue(
        queue_url=config.TRANSFORM_JOBS_QUEUE,
        job_type=Transform,
        large_payload_bucket=config.BIG_PAYLOADS_BUCKET,
    )
    load_jobs = SqsQueue(
        queue_url=config.LOAD_JOBS_QUEUE,
        job_type=Load,
        large_payload_bucket=config.BIG_PAYLOADS_BUCKET,
    )
    history_jobs = SqsQueue(
        queue_url=config.HISTORY_JOBS_QUEUE,
        job_type=HistoryExtract,
        large_payload_bucket=config.BIG_PAYLOADS_BUCKET,
    )
    return SqsQueues(extract_jobs, transform_jobs, load_jobs, history_jobs)


def get_in_memory_queues():
    extract_jobs = InMemoryQueue(job_type=Extract)
    transform_jobs = InMemoryQueue(job_type=Transform)
    load_jobs = InMemoryQueue(job_type=Load)
    history_jobs = InMemoryQueue(job_type=HistoryExtract)
    return InMemoryQueues(extract_jobs, transform_jobs, load_jobs, history_jobs)
