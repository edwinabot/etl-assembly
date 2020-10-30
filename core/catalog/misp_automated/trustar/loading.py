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
            # try to find by external ID
            existing_report = self.client.get_report_details(
                report.external_id, "external"
            )
        except HTTPError as ex:
            logger.warning(ex)
            existing_report = None

        try:
            # try to get the submission status
            status = (
                self.client.get_report_status(existing_report)
                if existing_report
                else self.client.get_report_status(report)
            )
        except HTTPError as ex:
            logger.warning(ex)
            status = None

        try:
            # try submitting
            submission_result = self.client.submit_report(report)
            logger.info(f"Report submitted successfuly, got ID: {submission_result.id}")
            try_updating = False if submission_result.id else True
        except Exception as ex:
            logger.info(f"Submission failed, tryiing updating: {ex}")
            try_updating = True

        try:
            # try to update or submit
            if (
                status and status.get("status", "UNKNOWN") == "SUBMISSION_SUCCESS"
            ) or try_updating:
                update_result = self.client.update_report(report)
                logger.info(f"Report submitted successfuly, got ID: {update_result.id}")
        except HTTPError as e:
            logger.error(e)


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
