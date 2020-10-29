from datetime import datetime, timedelta, timezone

from trustar import TruStar, datetime_to_millis

from core.registry import Job
from core.logs import get_logger


logger = get_logger(__name__)


class StationExtractor:
    """
    Light wrapper for extraction methods in the TruSTAR SDK
    """

    TIME_DELTA = timedelta(minutes=5)
    MAX_REPORT_COUNT = 10000

    def __init__(self, job: Job) -> None:
        self.job = job
        self._build_client()

    def _build_client(self):
        ts_conf = self.job.user_conf.source_conf
        ts_conf.update(self.job.user_conf.source_secrets)
        self.client = TruStar(config=ts_conf)

    def get_current_datetime(self):
        return datetime.now(timezone.utc)

    def get_reports(self):
        """
        Submits a new report to TruSTAR.
        :param report: a Report object
        :return: None
        """
        try:
            window = self.job.user_conf.source_conf.get("timewindow", None)
            if window:
                to = window["to"]
                since = window["from"]
            else:
                # If there is no timewindow build one of 5 minutes or less
                to = self.get_current_datetime()
                since = self.job.last_run
                if not since:
                    since = to - self.TIME_DELTA
                elif (to - since) > timedelta(minutes=5):
                    to = since + self.TIME_DELTA

            reports = self.consume_all_report_pages(since, to)
            logger.info(f"Got {len(reports)} since {since}")

            # https://docs.trustar.co/api/v13/reports/get_report_details.html
            results = []
            logger.debug("Getting reports details")
            for report in reports:
                try:
                    logger.debug(f"Getting details for report {report.id}")
                    full_report = self.client.get_report_details(report.id)
                    results.append(full_report)
                except Exception as e:
                    logger.warning(e)
                    results.append(report)
            return results, to
        except Exception as e:
            logger.error(e)

    def is_report_fully_processed(self, report):
        result = self.client.get_report_status(report)
        return result["status"] == "SUBMISSION_SUCCESS"

    def consume_all_report_pages(self, from_time, to_time=None, max_report_count=None):
        logger.debug(
            f"Pulling reports from {from_time.isoformat()}"
            f" to {to_time.isoformat() if to_time else ''}"
        )
        if not max_report_count:
            max_report_count = self.MAX_REPORT_COUNT
        reports = []
        page = 0
        there_is_more = True
        while there_is_more:
            response = self.client.search_reports_page(
                enclave_ids=self.job.user_conf.source_conf.get("enclave_ids"),
                from_time=datetime_to_millis(from_time),
                to_time=datetime_to_millis(to_time) if to_time else None,
                page_size=100,
                page_number=page,
            )
            if response.items:
                reports.extend(response.items)

            if not response.items:
                # stop if there are no more reports
                there_is_more = False
                logger.debug("No more items")
            elif len(reports) >= max_report_count:
                # stop if we reached the maximum allowed number of reports
                logger.debug(
                    f"Report pull limit reached for "
                    f"job {self.job.id} {self.job.description}"
                )
                there_is_more = False
                reports = reports[:max_report_count]
            else:
                # ask the pagination if there are more
                there_is_more = response.has_more_pages()
            page += 1
        logger.debug(f"Pulled {len(reports)}")
        return reports

    def get_enclave_tags(self, report):
        logger.debug(f"Getting tags for report {report.id}")
        return list(self.client.get_enclave_tags(report.id))

    def get_indicators_for_report(self, report):
        iocs = []
        there_is_more = True
        page = 0

        logger.debug(f"Getting IOCs for report {report.id}")
        while there_is_more:
            response = self.client.get_indicators_for_report_page(
                report.id, page_number=page, page_size=1000
            )
            if response.items:
                iocs.extend(response.items)
            else:
                there_is_more = False
                logger.debug(f"No more IOCs for report {report.id} stopping.")
                continue

            if not response.has_more_pages():
                there_is_more = False
                logger.debug(f"No more IOCs for report {report.id} stopping.")
            else:
                page += 1
        return iocs

    def get_iocs_metadata(self, iocs: list):
        try:
            result = self.client.get_indicators_metadata(iocs)
            return result
        except Exception as e:
            logger.warning("Failed to retrieve iocs metadata")
            logger.warning(e)
            return iocs

    def get_enclave_iocs(self):
        results = []
        # Prepare enclave ids list
        enclave_ids = self.job.user_conf.source_conf.get("enclave_ids")
        # If not available get all enclaves for the user and populate
        if not enclave_ids:
            logger.info("No enclave ids provided. Retrieving all user enclaves ids")
            enclaves = (
                self.client.get_user_enclaves()
            )  # if filter out read only enclaves?
        else:
            enclaves = [
                e for e in self.client.get_user_enclaves() if e.id in enclave_ids
            ]

        # retrieve enclave iocs
        for enclave in enclaves:
            try:
                logger.info(
                    f"Extracting IOCs from enclave {enclave.name} id {enclave.id} "
                    f"since {self.job.last_run}"
                )
                indicators = list(
                    self.client.search_indicators(
                        enclave_ids=[enclave.id],
                        from_time=datetime_to_millis(self.job.last_run),
                    )
                )
                results.append(
                    {
                        "enclave": enclave.to_dict(),
                        "iocs": [i.to_dict() for i in indicators],
                    }
                )
            except Exception as ex:
                logger.error(
                    f"Failed to pull iocs from from enclave {enclave.name} "
                    f"id {enclave.id} with error {ex}"
                )
        return results


def pull_reports(job: Job):
    """
    Pulls all reports since last run from all enclaves
    """
    try:
        report_deeplink_base = job.user_conf.source_conf["report_deeplink_base"]
        report_deeplink_base = report_deeplink_base.strip("/")
        extractor = StationExtractor(job)
        results = []

        # TODO: validate that user has read access for the enclaves
        reports, to_datetime = extractor.get_reports()

        for report in reports:
            try:
                if extractor.is_report_fully_processed(report):
                    tags = extractor.get_enclave_tags(report)
                    indicators = extractor.get_indicators_for_report(report)
                    indicators = extractor.get_iocs_metadata(indicators)
                else:
                    tags = []
                    indicators = []
                results.append(
                    {
                        "report": report.to_dict(),
                        "tags": [t.to_dict() for t in tags],
                        "indicators": [i.to_dict() for i in indicators],
                        "deeplink": "/".join((report_deeplink_base, report.id)),
                    }
                )
            except Exception as e:
                logger.warning(f"While processing report {report}: {e}")

        return results, to_datetime
    except Exception as ex:
        logger.error(f"Failed to extract repors for job {job.id}")
        raise ex


def pull_enclaves_iocs(job: Job):
    try:
        extractor = StationExtractor(job)
        # TODO: validate that user has read access for the enclaves
        results = extractor.get_enclave_iocs()
        return results
    except Exception as ex:
        logger.error(f"Failed to extract IOCs from enclaves for job {job.id}")
        raise ex
