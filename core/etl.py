from abc import ABC, abstractmethod
import importlib
import json
from datetime import datetime
from queue import Empty, Queue
from typing import Union, List

import boto3
import sqs_extended_client  # noqa: F401

from core.registry import Job
from core.logs import get_logger

logger = get_logger(__name__)


class BaseJob:
    """
    Base Job class for all type of jobs.
    """

    def __init__(self, callable_path: str, callable_arguments: dict):
        """
        Parameters
        ----------
        callable_path :
            callable in the module
        callable_arguments : dict
            dictionary containing the arguments to be passed to the callable
        """
        if not isinstance(callable_arguments, dict):
            raise TypeError("job_arguments param must be a dict")
        self._callable_arguments = callable_arguments
        self._callable_path = callable_path
        self._load_job_callable(callable_path)

    def run(self):
        """Invoques the configured callable for this job with the provided parameters"""
        return self._job_callable(**self._callable_arguments)

    def serialize(self):
        """Serializes this job to json string

        Returns
        -------
        bytes
            bytes string representation of this job
        """
        serialized = json.dumps(self.as_dict())
        return serialized

    def as_dict(self):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, source_dict):
        raise NotImplementedError

    @classmethod
    def deserialize(cls, bytestream: str) -> "Job":
        """Deserializes the provided json_string

        Returns
        -------
        Job
            A Job object
        """
        deserialized = json.loads(bytestream)
        pythonified = cls.from_dict(deserialized)
        return pythonified

    @classmethod
    def build(cls, *args, **kwargs):
        """Factory method to instantiate Jobs"""
        return cls(*args, **kwargs)

    def _load_job_callable(self, callable_path: str):
        """Imports the module and gets the callable from it"""
        # importlib.invalidate_caches()
        # TODO: sanitization of the code is critical here. What are we loading?
        exploded_path = ["core", "catalog"]
        exploded_path.extend(callable_path.split("."))  # misp.extraction.pull_feeds
        module = importlib.import_module(".".join(exploded_path[:-1]))
        self._job_callable = getattr(module, exploded_path[-1])


class Extract(BaseJob):
    """
    This is for performing Extraction Jobs from the configured source
    """

    def __init__(self, job: Job):
        """
        Params
        ------
        job : Job
            The job configuration
        """
        super().__init__(
            callable_path=job.template.extract, callable_arguments={"job": job},
        )
        self.job = job

    def update_extraction_datetime(self, extraction_datetime: datetime):
        self.job.last_run = extraction_datetime
        self.job.save()

    def as_dict(self):
        return {"job": self.job.to_dict()}

    @classmethod
    def from_dict(cls, source_dict):
        job = Job.from_dict(source_dict["job"])
        return cls(job)


class Transform(BaseJob):
    """
    This is for perform Transformation on the extracted
    data as per the job configuration
    """

    def __init__(self, job: Job, extracted_data):
        """
        Params
        ------
        job : Job
            The job configuration
        extracted_data: dict
            The data to be transformed and data about the data
        """
        if not extracted_data:
            raise Exception(f"No data to Transform for job: {job.id}")

        self.job = job
        self.extracted_data = extracted_data
        super().__init__(
            callable_path=self.job.template.transform,
            callable_arguments={"extracted_data": self.extracted_data},
        )

    def as_dict(self):
        return {"job": self.job.to_dict(), "extracted_data": self.extracted_data}

    @classmethod
    def from_dict(cls, source_dict):
        job = Job.from_dict(source_dict["job"])
        return cls(job, source_dict["extracted_data"])


class Load(BaseJob):
    """
    This is for Loading data to the configured destination.
    """

    def __init__(self, job: Job, transformed_data: dict):
        """
        Params
        ------
        job : Job
            The job configuration
        transformed_data:
            The data to be loaded to the destination and data about the data
        """
        self.job = job
        self.transformed_data = transformed_data
        super().__init__(
            callable_path=self.job.template.load, callable_arguments={"job": self},
        )

    def as_dict(self):
        return {"job": self.job.to_dict(), "transformed_data": self.transformed_data}

    @classmethod
    def from_dict(cls, source_dict):
        job = Job.from_dict(source_dict["job"])
        return cls(job, source_dict["transformed_data"])


class AbstractQueue(ABC):
    @abstractmethod
    def put(self, jobs: List[Union[Extract, Transform, Load]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self) -> Union[Extract, Transform, Load]:
        raise NotImplementedError


class InMemoryQueue(AbstractQueue):
    def __init__(self, job_type: Union[Extract, Transform, Load]):
        self._q: Queue = Queue()
        self.job_type = job_type

    def put(self, jobs: List[Union[Extract, Transform, Load]]):
        for j in jobs:
            self._q.put(j.serialize(), block=False)

    def get(self) -> Union[Extract, Transform, Load]:
        return self.job_type.deserialize(self._q.get(block=False))


class SqsQueue(AbstractQueue):
    MESSAGE_POINTER_CLASS = "com.amazon.sqs.javamessaging.MessageS3Pointer"

    def __init__(
        self,
        queue_url: str,
        job_type: Union[Extract, Transform, Load],
        large_payload_bucket: str = None,
    ):
        self.queue_url = queue_url
        self.sqs = boto3.client("sqs")
        self.job_type = job_type
        if large_payload_bucket:
            self.sqs.large_payload_support = large_payload_bucket
            self.sqs.always_through_s3 = True

    def put(self, jobs: List[Union[Extract, Transform, Load]]):
        # Send message to SQS queue
        for job in jobs:
            serialized_job = job.serialize()
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=serialized_job,
                MessageGroupId="assembly-messages",
            )
            logger.debug(f"Queued {job.job.id} with MessageId {response['MessageId']}")

    def get(self) -> Union[Extract, Transform, Load]:
        response = self.get_raw()
        message = response["Messages"][0]
        job = self.build_job(message["Body"])
        receipt_handle = message["ReceiptHandle"]
        # Delete received message from queue
        self.delete_message(receipt_handle)
        return job

    def build_job(self, message_body):
        try:
            deserialized_message = json.loads(message_body)
        except json.decoder.JSONDecodeError:
            message_body = message_body.replace("'", '"')
            deserialized_message = json.loads(message_body)
        if (
            isinstance(deserialized_message, list)
            and len(deserialized_message) == 2
            and deserialized_message[0] == self.MESSAGE_POINTER_CLASS
        ):
            raw_payload = deserialized_message[1]
            payload = self.get_payload_from_s3(
                raw_payload["s3BucketName"], raw_payload["s3Key"]
            )
            job = self.job_type.deserialize(payload)
        else:
            job = self.job_type.deserialize(message_body)
        return job

    def get_payload_from_s3(self, bucket_name, object_key):
        """
        Retrieves the configuration file from the specified bucket,
        parses the JSON to a list of dicts
        """
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(bucket_name)
        obj = bucket.Object(key=object_key)
        logger.debug(f"Getting {bucket}/{obj}")
        response = obj.get()
        lines: bytes = response["Body"].read()
        return lines

    def get_raw(self) -> dict:
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=["All"],
            AttributeNames=["ALL"],
        )
        if "Messages" not in response:
            raise Empty
        logger.debug(response)
        return response

    def delete_message(self, receip_handle):
        self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receip_handle)
