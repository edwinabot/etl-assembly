from datetime import datetime, timedelta, timezone
from pymisp import PyMISP, PyMISPError

from core.registry import Job
from core.logs import get_logger


logger = get_logger(__name__)

MAX_PULL_REPORTS = 500


class FeedClient:
    TIME_DELTA = timedelta(minutes=5)

    def __init__(self, job: Job) -> None:
        self.job = job

    def get_misp_client(self):
        # Initializing MISP connection
        misp_conn = PyMISP(
            url=self.job.user_conf.source_conf.get("url"),
            key=self.job.user_conf.source_secrets.get("key"),
            ssl=self.job.user_conf.source_conf.get("verify_server_cert", False),
        )

        if misp_conn and hasattr(misp_conn, "get_version"):
            misp_version = misp_conn.get_version()
            logger.info("MISP version {}".format(misp_version.get("version")))

        return misp_conn

    def query_misp(self, misp_conn: PyMISP, since: datetime, to: datetime):
        """Pull data from the MISP API and return response.

        :param interval: time interval (e.g - 24h, 240m, 30.6m, etc)
        :return response: response data
        """
        response = None
        try:
            # Fetch all MISP events
            not_this_tags = misp_conn.build_complex_query(
                not_parameters=["Enclave", "TruSTAR"]
            )
            logger.debug(
                f"Searching MISP Events from {since.isoformat()} to {to.isoformat()}"
            )
            response = misp_conn.search(
                timestamp=(since, to),
                tag=not_this_tags,
                pythonify=True,
            )
        except PyMISPError as pyexe:
            logger.error(f"MISP Communication Error : {pyexe}")
        except Exception as exe:
            logger.exception("MISP client Error : {}", (exe,), exc_info=True)
        finally:
            return response

    @staticmethod
    def clean_response(response):
        results = None
        if not response:
            logger.warning("Empty response received")
        elif isinstance(response, list):
            results = response
        elif isinstance(response, dict) and response.get("errors"):
            logger.error(
                "MISP Client Error. Response Content - {}".format(
                    response.get("errors", "")
                )
            )
        elif isinstance(response, dict) and response.get("response"):
            results = response["response"]
        return results

    def get_current_datetime(self):
        return datetime.now(timezone.utc)

    def pull_feeds(self):
        """
        Pulls MISP Events.
        It exclude al events tagged as TruSTAR
        Additionally checks that the Event is not an Enclave Event
        """
        results = None
        to = None
        try:
            misp_client = self.get_misp_client()
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

            # Fetch MISP events data
            response = self.query_misp(misp_client, since, to)
            if response:
                results = self.clean_response(response)
                # Sort data list based on timestamp column. Latest events on top
                results = sorted(results, key=lambda k: k.timestamp, reverse=True)
            else:
                results = []

        except Exception as ex:
            logger.error(f"Could not query on MISP Client Error: {ex}")
            raise ex
        else:
            return [r.to_json() for r in results], to


def pull_feeds(job: Job):
    try:
        feed_client = FeedClient(job)
        results, to_datetime = feed_client.pull_feeds()
        return results, to_datetime
    except Exception as ex:
        logger.error(f"Failed to pull feed for job {job.id}")
        raise ex
