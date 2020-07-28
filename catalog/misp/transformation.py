import json

from trustar import Report
from pymisp import MISPEvent, MISPObject

from logs import get_logger

logger = get_logger(__name__)


class MispToTrustar:
    def __init__(self, feed: list, *args, **kwargs) -> None:
        self.feed = feed

        self.allowed_tag_name_length = kwargs.get("allowed_tag_name_length", 20)

    def process_event(self, event: dict):
        report, attribute_tags = None, None
        try:
            report = Report(
                title=event["id"],
                body=json.dumps(event),
                time_began=event["date"],
                external_id=event["uuid"],
            )

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


class TrustarToMisp:
    @staticmethod
    def reports_to_misp_events(extracted_reports):
        """
        Converts TruSTAR reports into their own MISP events, including the report
        tags and indicators as part of the object that attaches to the MISP event
        """
        events = []
        # Iterate through each TruSTAR report and create MISP events for each
        for element in extracted_reports:
            try:
                logger.info(f"Tranforming {element}")
                # Initialize and set MISPEvent()
                report = element["report"]
                tags = element["tags"]
                indicators = element["indicators"]

                event = MISPEvent()
                event.info = report.title
                logger.debug(f"Generating a MISP event for {event.info}")

                # Get tags for report
                for tag in tags:
                    event.add_tag(tag.name)
                    logger.debug(f"{tag.name} added to event")

                # Create MISP TruSTAR object to add indicators to event
                logger.debug(f"Generating a MISP object for {event.info}")
                obj = MISPObject("trustar_report", standalone=False, strict=True)

                # Get indicators for report
                logger.debug(f"Adding indicators for {event.info} to MISP object")
                for indicator in indicators:
                    obj.add_attribute(indicator.type, indicator.value)
                event.add_object(obj)

                events.append(event)
            except KeyError as k:
                logger.error(f"Missing {k} in {element}")
            except Exception as e:
                logger.error(
                    f"Failed to transform TruSTAR report {element['report']} "
                    f"to MISP event - {e}"
                )
        return events

    @staticmethod
    def ioc_list_to_misp_object_attributes(extacted_iocs):
        """
        Returns a MISPObject with the extracted IOCs as attributes
        """
        obj = MISPObject("trustar_report", standalone=False, strict=True)
        for indicator in extacted_iocs:
            obj.add_attribute(indicator.type, indicator.value)
        return obj


def for_trustar_reports(extracted_data):
    transformer = MispToTrustar(extracted_data)
    processed_feed = transformer.process_feed()
    return processed_feed


def ts_reports_to_misp_event(extracted_data):
    result = TrustarToMisp.reports_to_misp_events(extracted_data)
    return result


def ts_enclave_ioc_to_misp_attributes(extracted_data: dict):
    try:
        for k, v in extracted_data.items():
            obj = TrustarToMisp.ioc_list_to_misp_object_attributes(v)
            extracted_data[k] = obj
        return extracted_data
    except Exception as ex:
        logger.error("Failed to transform data")
        logger.exception(ex)
