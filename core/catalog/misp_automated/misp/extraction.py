from datetime import datetime
from pymisp import PyMISP, PyMISPError

from core.registry import Job
from core.logs import get_logger


logger = get_logger(__name__)

MAX_PULL_REPORTS = 500


class FeedClient:
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

    def query_misp(self, misp_conn: PyMISP, since: datetime):
        """ Pull data from the MISP API and return response.

        :param interval: time interval (e.g - 24h, 240m, 30.6m, etc)
        :return response: response data
        """
        response = None
        try:
            # Fetch all MISP events
            not_this_tags = misp_conn.build_complex_query(
                not_parameters=["Enclave", "TruSTAR"]
            )
            response = misp_conn.search(
                timestamp=since, tag=not_this_tags, pythonify=True,
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

    def pull_feeds(self):
        """
        Pulls MISP Events.
        It exclude al events tagged as TruSTAR
        Additionally checks that the Event is not an Enclave Event
        """
        results = None
        try:
            misp_client = self.get_misp_client()
            since = self.job.last_run if self.job.last_run else "30d"

            # Fetch MISP events data
            response = self.query_misp(misp_client, since)
            if response:
                results = self.clean_response(response)
                # Sort data list based on timestamp column. Latest events on top
                results = sorted(response, key=lambda k: k.timestamp, reverse=True)
            else:
                logger.warning("Client Error or empty response received")

        except Exception as ex:
            logger.error(f"Could not query on MISP Client Error: {ex}")
            raise ex
        else:
            return [r.to_json() for r in results]


def pull_feeds(job: Job):
    try:
        feed_client = FeedClient(job)
        return feed_client.pull_feeds()
    except Exception as ex:
        logger.error(f"Failed to pull feed for job {job.id}")
        raise ex
