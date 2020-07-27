import json

from trustar import Report

from logs import get_logger

logger = get_logger(__name__)


class EventFeedToTrustarReportTransformation:
    def __init__(self, feed: list, *args, **kwargs) -> None:
        self.feed = feed

        self.allowed_tag_name_length = kwargs.get("allowed_tag_name_length", 20)

    def process_event(self, event: dict):
        report, attribute_tags = None, None
        try:
            report = Report(title=event["id"],
                            body=json.dumps(event),
                            time_began=event["timestamp"],
                            external_id=event["uuid"])

            # Tags are fetched from 2 sources.
            # 1. Attribute Tags 2. Object Attribute Tags
            # 1. Get attributes tags
            attribute_tags = self.get_tags_from_attributes(event.get("Attribute", []))

            # 2. Get Object Attribute Tags
            # Iterate through objects of event to get attributes
            for objects in event.get("Object", []):
                # Append the tags from object attribute
                attribute_tags = attribute_tags.union(
                    self.get_tags_from_attributes(objects.get("Attribute", []))
                )
        except KeyError as ke:
            logger.warning(f"{ke} not in event {event}")
        finally:
            return report, attribute_tags

    def process_feed(self):
        """
        Using the MISP response in the given
        filepath, processes it into a TruSTAR incident
        report. Opens the file and reads.
        Populates report dict with required fields.

        :param file_path: path of file
        :return: dict for report, that has keys read by TruSTAR API client
        """
        results = []
        for item in self.feed:
            report, tags = self.process_event(item["Event"])
            results.append({"report": report, "tags": tags})
        return results

    def get_tags_from_attributes(self, list_attributes):
        """
        Get tags from attributes of events.

        :param list_attributes: list of attributes
        :return: set of unique tags
        """
        attribute_tags = set()

        # Iterate through attribute of events to get tags
        for attributes in list_attributes:
            for tag in attributes.get("Tag", []):
                # Adding tags only if length of tag name <= 20.
                if len(tag["name"]) <= self.allowed_tag_name_length:
                    attribute_tags.add(tag["name"])
                else:
                    logger.info(
                        "Ignoring Tag name {} of length {}".format(
                            tag["name"], len(tag["name"])
                        )
                    )

        return attribute_tags


def for_trustar_reports(extracted_data):
    transformer = EventFeedToTrustarReportTransformation(extracted_data)
    processed_feed = transformer.process_feed()
    return processed_feed
