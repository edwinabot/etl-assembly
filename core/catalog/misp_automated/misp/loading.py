from pymisp import PyMISP, MISPEvent
from trustar.models.enclave import Enclave, EnclavePermissions

from core.registry import Job
from core.etl import Load
from core.logs import get_logger

logger = get_logger(__name__)


class MISPLoader:
    def __init__(self, job: Job) -> None:
        self.job = job
        self._build_client()

    def _build_client(self):
        conf = self.job.user_conf.destination_conf
        secret = self.job.user_conf.destination_secrets
        self.client = PyMISP(
            url=conf["url"], key=secret["key"], ssl=conf.get("ssl", True)
        )

    @staticmethod
    def build_enclave_event(enclave: Enclave):
        event = MISPEvent()
        event.uuid = enclave.id
        event.info = f"TruSTAR Enclave: {enclave.name}"
        event.add_tag("TruSTAR")
        event.add_tag("Enclave")
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
    results: dict = {"success": [], "error": []}
    for element in job.transformed_data:
        try:
            event = MISPEvent()
            event.from_json(element)
            loader.upsert_event(event)
            results["success"].append(element)
        except Exception as ex:
            logger.exception(ex)
            results["error"].append((element, ex))
    return results


def load_to_enclave_event(job: Load):
    """
    Loads objects with its attributes to the corresponding enclave event.
    If the enclave event doesn't exists it will be created
    """
    loader = MISPLoader(job=job.job)
    results: dict = {"success": [], "error": []}
    for data in job.transformed_data:
        enclave = Enclave.from_dict(data['enclave'])
        attributes = data['iocs']
        try:
            event = loader.get_event(enclave.id)
            if not event:
                event = loader.build_enclave_event(enclave)
            event.add_object(attributes)
            loader.upsert_event(event)
            results["success"].append((enclave, attributes))
        except Exception as ex:
            logger.exception(ex)
            results["error"].append((enclave, attributes, ex))
    return results
