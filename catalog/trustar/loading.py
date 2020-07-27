from requests import HTTPError
from trustar import TruStar
from trustar.models import Report

from logs import get_logger

from etl import Load, Job

logger = get_logger(__name__)


class StationLoader:
    def __init__(self, sdk_conf: Job) -> None:
        self.sdk_conf = sdk_conf
        self._build_client()

    def _build_client(self):
        ts_conf = self.sdk_conf.user_conf.destination_conf
        ts_conf.update(self.sdk_conf.user_conf.destination_secrets)
        self.client = TruStar(config=ts_conf)

    def submit_report(self, report: Report):
        """
        Submits a new report to TruSTAR.
        :param report: a Report object
        :return: None
        """
        try:
            response = self.client.submit_report(report)
            logger.info(f"Report submitted successfuly, got ID: {response.id}")
        except HTTPError as e:
            logger.error(f"Something went wrong: {e}")


def load_reports(job: Load):
    loader = StationLoader(sdk_conf=job.job)
    for element in job.transformed_data:
        loader.submit_report(element.get("report"))
