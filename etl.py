import pickle
import importlib

from queue import Queue


class Job:
    def __init__(self, catalog_module, callable_name, callable_arguments):
        if not isinstance(callable_arguments, dict):
            raise TypeError("job_arguments param must be a dict")
        self._callable_arguments = callable_arguments
        self._load_job_callable(catalog_module, callable_name)

    def run(self):
        return self._job_callable(**self._callable_arguments)

    def serialize(self):
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, bytestream):
        return pickle.loads(bytestream)

    @classmethod
    def build(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def _load_job_callable(self, catalog_module, callable_name):
        # importlib.invalidate_caches()
        module = importlib.import_module(f"catalog.{catalog_module}")
        self._job_callable = getattr(module, callable_name)


class Extract(Job):
    def __init__(self, job_config):
        super().__init__(
            catalog_module=job_config.template.source,
            callable_name=job_config.template.extract,
            callable_arguments={"job_config": job_config},
        )
        self.job_config = job_config


class Transform(Job):
    def __init__(self, job_config, extracted_data):
        super().__init__(
            catalog_module=job_config.template.source,
            callable_name=job_config.template.transform,
            callable_arguments={"job_config": job_config},
        )
        self.job_config = job_config
        self.extracted_data = extracted_data
        print("Transform initialized")


class Load(Job):
    def __init__(self, job_config, transformed_data):
        super().__init__(
            catalog_module=job_config.template.destination,
            callable_name=job_config.template.load,
            callable_arguments={"job_config": job_config},
        )
        self.job_config = job_config
        self.transformed_data = transformed_data
        print("Load initialized")


class AbstractQueue:
    def __init__(self):
        self._q = Queue()

    def put(self, job: Job):
        self._q.put(job.serialize())

    def get(self):
        return self._q.get()

    def deserialize(self, message):
        raise NotImplementedError


class ExtractQueue(AbstractQueue):
    def deserialize(self, message):
        return Extract.deserialize(message)

    def get(self):
        element = super().get()
        return Extract.deserialize(element)


class TransformQueue(AbstractQueue):
    def deserialize(self, message):
        return Transform.deserialize(message)

    def get(self):
        element = super().get()
        return Transform.deserialize(element)


class LoadQueue(AbstractQueue):
    def deserialize(self, message):
        return Load.deserialize(message)

    def get(self):
        element = super().get()
        return Load.deserialize(element)
