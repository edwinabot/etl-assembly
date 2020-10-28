from requests import HTTPError
from trustar import TruStar, Report

from core.logs import get_logger
from core.etl import Load, Job

logger = get_logger(__name__)


class StationLoader:
    def __init__(self, job: Job) -> None:
        self.job = job
        self._build_client()

    def _build_client(self):
        ts_conf = self.job.user_conf.destination_conf
        ts_conf.update(self.job.user_conf.destination_secrets)
        self.client = TruStar(config=ts_conf)

    def submit_report(self, report: Report):
        """
        Submits a new report to TruSTAR.
        :param report: a Report object
        :return: None
        """
        try:
            if (
                self.client.get_report_status(report).get("status")
                == "SUBMISSION_SUCCESS"
            ):
                response = self.client.update_report(report)
            else:
                response = self.client.submit_report(report)
            logger.info(f"Report submitted successfuly, got ID: {response.id}")
        except HTTPError as e:
            logger.error(f"Something went wrong: {e}")


def load_reports(job: Load):
    loader = StationLoader(job=job.job)
    results: dict = {"success": [], "error": []}
    for element in job.transformed_data:
        try:
            loader.submit_report(Report.from_dict(element.get("report")))
            results["success"].append(element)
        except Exception as ex:
            logger.exception(ex)
            results["error"].append((element, ex))
    return results
