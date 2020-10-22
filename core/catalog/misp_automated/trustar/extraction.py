from datetime import datetime, timedelta, timezone

from trustar import TruStar, datetime_to_millis

from core.registry import Job
from core.logs import get_logger


logger = get_logger(__name__)


class StationExtractor:
    """
    Light wrapper for extraction methods in the TruSTAR SDK
    """

    FIRST_RUN_TIMEDELTA = timedelta(days=30)
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
            to = self.get_current_datetime()
            since = (
                self.job.last_run
                if self.job.last_run
                else to - self.FIRST_RUN_TIMEDELTA
            )
            if (to - since).days:
                reports = self._get_reports_partinioning_timewindow(since, to)
            else:
                reports = self._consume_all_report_pages(since)
            logger.info(f"Got {len(reports)} since {since}")
            return reports
        except Exception as e:
            logger.error(f"Something went wrong: {e}")

    def _get_reports_partinioning_timewindow(self, since, to):
        reports = []
        timedelta_in_hours = (to - since).days * 24
        windows = [
            {
                "from": since + timedelta(hours=i * 12),
                "to": since + timedelta(hours=(i * 12) + 12),
            }
            for i in range(0, int(timedelta_in_hours / 12) + 1)
        ]
        for window in windows:
            reports.extend(
                self._consume_all_report_pages(
                    window["from"], window["to"], self.MAX_REPORT_COUNT - len(reports)
                )
            )
            if len(reports) >= self.MAX_REPORT_COUNT:
                break
        return reports

    def _consume_all_report_pages(self, from_time, to_time=None, max_report_count=None):
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
                page_size=1000,
                page_number=page,
            )
            if response.items:
                reports.extend(response.items)

            if not response.items:
                there_is_more = False
            elif len(reports) >= max_report_count:
                there_is_more = False
                reports = reports[:max_report_count]
            else:
                there_is_more = response.has_more_pages()
            page += 1
        return reports

    def get_enclave_tags(self, report):
        return list(self.client.get_enclave_tags(report.id))

    def get_indicators_for_report(self, report):
        # increase page size to reduce call number
        return list(self.client.get_indicators_for_report(report.id))

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
        extractor = StationExtractor(job)
        report_deeplink_base = job.user_conf.source_conf["report_deeplink_base"].strip(
            "/"
        )
        results = []

        reports = extractor.get_reports()

        for report in reports:
            tags = extractor.get_enclave_tags(report)
            indicators = extractor.get_indicators_for_report(report)
            results.append(
                {
                    "report": report.to_dict(),
                    "tags": [t.to_dict() for t in tags],
                    "indicators": [i.to_dict() for i in indicators],
                    "deeplink": "/".join((report_deeplink_base, report.id)),
                }
            )

        return results
    except Exception as ex:
        logger.error(f"Failed to extract repors for job {job.id}")
        raise ex


def pull_enclaves_iocs(job: Job):
    try:
        extractor = StationExtractor(job)
        results = extractor.get_enclave_iocs()
        return results
    except Exception as ex:
        logger.error(f"Failed to extract IOCs from enclaves for job {job.id}")
        raise ex
