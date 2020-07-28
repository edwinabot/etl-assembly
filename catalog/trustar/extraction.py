from datetime import datetime, timedelta

from trustar import TruStar, datetime_to_millis
from registry import Job
from logs import get_logger


logger = get_logger(__name__)


class StationExtractor:
    """
    Light wrapper for extraction methods in the TruSTAR SDK
    """

    def __init__(self, job: Job) -> None:
        self.job = job
        self._build_client()

    def _build_client(self):
        ts_conf = self.job.user_conf.source_conf
        ts_conf.update(self.job.user_conf.source_secrets)
        self.client = TruStar(config=ts_conf)

    def get_reports(self):
        """
        Submits a new report to TruSTAR.
        :param report: a Report object
        :return: None
        """
        try:
            since = (
                self.job.last_run
                if self.job.last_run
                else datetime.utcnow() - timedelta(days=30)
            )
            response = self.client.get_reports(
                is_enclave=True, from_time=datetime_to_millis(since),
            )
            reports = list(response)
            logger.info(f"Got {len(reports)} since {since}")
            return reports
        except Exception as e:
            logger.error(f"Something went wrong: {e}")

    def get_enclave_tags(self, report):
        return list(self.client.get_enclave_tags(report.id))

    def get_indicators_for_report(self, report):
        return list(self.client.get_indicators_for_report(report.id))

    def get_enclave_iocs(self):
        results = {}
        # Prepare enclave ids list
        enclave_ids = self.job.user_conf.source_conf.get("enclave_ids")
        # If not available get all enclaves for the user and populate
        if not enclave_ids:
            logger.info("No enclave ids provided. Retrieving all user enclaves ids")
            enclaves = self.client.get_user_enclaves()
            enclave_ids = [e.id for e in enclaves]  # if e.read?

        # retrieve enclave iocs
        for enclave_id in enclave_ids:
            try:
                logger.info(
                    f"Extracting IOCs from enclave {enclave_id} "
                    f"since {self.job.last_run}"
                )
                indicators = list(
                    self.client.search_indicators(
                        enclave_ids=[enclave_id],
                        from_time=datetime_to_millis(self.job.last_run),
                    )
                )
                results.update({enclave_id: indicators})
            except Exception as ex:
                logger.error(
                    f"Failed to pull iocs from enclave {enclave_id} with error {ex}"
                )
        return results


def pull_reports(job: Job):
    """
    Pulls all reports since last run from all enclaves
    """
    try:
        extractor = StationExtractor(job)
        results = []

        reports = extractor.get_reports()

        for report in reports:
            tags = extractor.get_enclave_tags(report)
            indicators = extractor.get_indicators_for_report(report)
            results.append({"report": report, "tags": tags, "indicators": indicators})

        return results
    except Exception as ex:
        logger.error(f"Failed to extract repors for job {job.id}")
        logger.exception(ex)


def pull_enclaves_iocs(job: Job):
    try:
        extractor = StationExtractor(job)
        results = extractor.get_enclave_iocs()
        return results
    except Exception as ex:
        logger.error(f"Failed to extract IOCs from enclaves for job {job.id}")
        logger.exception(ex)
