from pymisp import PyMISP, MISPEvent

from registry import Job
from etl import Load
from logs import get_logger

logger = get_logger(__name__)


class MISPLoader:
    def __init__(self, job: Job) -> None:
        self.job = job
        self._build_client()

    def _build_client(self):
        conf = self.job.user_conf.destination_conf
        secret = self.job.user_conf.destination_secrets
        self.client = PyMISP(url=conf["url"], key=secret["key"])

    def build_enclave_event(self, enclave_id: str):
        event = MISPEvent()
        event.uuid = enclave_id
        event.info = f"Enclave {enclave_id}"
        event.add_tag("TruSTAR Enclave")
        event.add_tag(f"trustar_enclave_id:{enclave_id}")
        logger.info(f"Generating a MISP event for {event.info}")
        return event

    def get_event(self, event):
        response = self.client.get_event(event, pythonify=True)
        if isinstance(response, dict) and "errors" in response:
            logger.warning(f"Failed to retrieve Event {event}")
            response = None
        return response

    def upsert_event(self, event: MISPEvent):
        if hasattr(event, "id") and event.id:
            event = self.client.update_event(event, pythonify=True)
        else:
            event = self.client.add_event(event, pythonify=True)
        # If there's an error, RAISE HELL!!!
        if isinstance(event, dict) and "errors" in event:
            raise Exception(f"{event}")
        else:
            logger.info(
                f"Upserted MISP event {event.info} UUID {event.uuid} id {event.id}"
            )
        return event


def load_events(job: Load):
    loader = MISPLoader(job=job.job)
    for element in job.transformed_data:
        loader.upsert_event(element)


def load_to_enclave_event(job: Load):
    """
    Loads objects with its attributes to the corresponding enclave event.
    If the enclave event doesn't exists it will be created
    """
    loader = MISPLoader(job=job.job)
    for k, v in job.transformed_data.items():
        try:
            event = loader.get_event(k)
            if not event:
                event = loader.build_enclave_event(k)
            event.add_object(v)
            loader.upsert_event(event)
        except Exception as ex:
            logger.exception(ex)
