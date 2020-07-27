from pymisp import PyMISP, PyMISPError

from logs import get_logger


logger = get_logger(__name__)

MAX_PULL_REPORTS = 500


class FeedClient:
    def __init__(self, job) -> None:
        self.job = job

    @staticmethod
    def get_time_interval_to_query(start_time, end_time):
        """
        Calculates the time interval to query based on
        stored state file.

        :param start_time: Start time
        :param end_time: End time
        :return: time interval (e.g - 24h, 240m, 30.6m, etc)
        """

        interval = "24h"
        try:
            from_time = int(start_time.timestamp())
            to_time = int(end_time.timestamp())
            epoch_sec_diff = to_time - from_time
            time_in_minutes = epoch_sec_diff // 60
            interval = "{}m".format(time_in_minutes)
        except Exception as exe:
            logger.exception("MISP Client Error - {}".format(exe), exc_info=True)
            # Do not fetch latest data
            interval = "0m"

        return interval

    def get_response_data(self):
        """ Pull data from the MISP API and return response.

        :param interval: time interval (e.g - 24h, 240m, 30.6m, etc)
        :return response: response data
        """
        results = None
        try:
            # Initializing MISP connection
            misp_conn = PyMISP(
                url=self.job.user_conf.source_conf.get("url"),
                key=self.job.user_conf.source_secrets.get("key"),
                ssl=self.job.user_conf.source_conf.get("verify_server_cert", False),
            )

            if misp_conn and hasattr(misp_conn, "get_version"):
                misp_version = misp_conn.get_version()
                logger.info("MISP version {}".format(misp_version.get("version")))

            # Fetch all MISP events
            interval = self.job.user_conf.source_conf.get("frequency")
            response = misp_conn.search(last=interval)
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

        except PyMISPError as pyexe:
            logger.error(f"MISP Communication Error : {pyexe}")
        except Exception as exe:
            logger.exception("MISP client Error : {}", (exe,), exc_info=True)
        finally:
            return results

    def pull_feeds(self):
        """
        Pulls MISP feeds.
        Saves the responses as files in the stash data dir.
        For the first iteration, feeds in the block of latest 24 hours is fetched
        For subsequent iterations, feeds later than saved time are fetched not
        more than 500.
        For any iteration, the timestamp of latest feed is persisted

        :param start_time: starting poll time in datetime format
        :param end_time: ending poll time in datetime format
        :param feeds_dir: dir where feeds will be saved

        :return: boolean for pull success
        """
        results = None
        try:
            # Fetch MISP events data
            response = self.get_response_data()

            # Event is in json format
            # Process each event
            if response:
                # Sort data list based on timestamp column. Latest events on top
                results = sorted(
                    response, key=lambda k: k["Event"]["timestamp"], reverse=True
                )

                # if len(sorted_data_list) > MAX_PULL_REPORTS:
                #     logger.warning(
                #         (
                #             f"Total {len(sorted_data_list)} events retrieved. "
                #             "Considering latest
                #              {len(sorted_data_list) - MAX_PULL_REPORTS} events only."
                #         )
                #     )

                # # Consider MAX_PULL_REPORTS report only
                # sorted_data_list = sorted_data_list[:MAX_PULL_REPORTS]
                # for event in sorted_data_list:
                #     try:
                #         save_response_file(event, feeds_dir)
                #     except Exception as exe:
                #         pull_success = False
                #         logger.exception(
                #             "MISP Client Error : {}. \n Row entry : {}".format(
                #                 exe, event
                #             ),
                #             exc_info=True,
                #         )

            else:
                logger.warning("Client Error or empty response received")

        except Exception as exe:
            logger.exception(
                f"Could not query on MISP Client Error: {exe}", exc_info=True
            )
        finally:
            self.persist_state()
            return results

    def persist_state(self):
        """
        State information are attributes of the Job... should go to job configs...
        Does Job Configs name makes sense still?
        Probably Job is the right one
        What about storing run info for each step? A table for run summaries?
        """
        logger.warning("Persisting state to be implemented")


def pull_feeds(job):
    feed_client = FeedClient(job)
    return feed_client.pull_feeds()
