import pickle
import importlib
from datetime import datetime
from queue import Queue

from registry import Job


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
        self._load_job_callable(callable_path)

    def run(self):
        """Invoques the configured callable for this job with the provided parameters"""
        return self._job_callable(**self._callable_arguments)

    def serialize(self):
        """Serializes this job

        Returns
        -------
        bytes
            bytes string representation of this job
        """
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, bytestream: bytes) -> "Job":
        """Deserializes the provided bytestream

        Returns
        -------
        Job
            A Job object
        """
        return pickle.loads(bytestream)

    @classmethod
    def build(cls, *args, **kwargs):
        """Factory method to instantiate Jobs"""
        return cls(*args, **kwargs)

    def _load_job_callable(self, callable_path: str):
        """Imports the module and gets the callable from it"""
        # importlib.invalidate_caches()
        # TODO: sanitization of the code is critical here. What are we loading?
        exploded_path = ["catalog"]
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


class BaseQueue:
    def __init__(self):
        self._q = Queue()

    def put(self, job: BaseJob):
        self._q.put(job.serialize())

    def get(self):
        return self._q.get()

    def deserialize(self, message):
        raise NotImplementedError


class ExtractQueue(BaseQueue):
    def deserialize(self, message):
        return Extract.deserialize(message)

    def get(self):
        element = super().get()
        return Extract.deserialize(element)


class TransformQueue(BaseQueue):
    def deserialize(self, message):
        return Transform.deserialize(message)

    def get(self):
        element = super().get()
        return Transform.deserialize(element)


class LoadQueue(BaseQueue):
    def deserialize(self, message):
        return Load.deserialize(message)

    def get(self):
        element = super().get()
        return Load.deserialize(element)
