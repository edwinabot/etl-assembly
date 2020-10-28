from trustar import Report, Tag, Indicator
from pymisp import MISPEvent, MISPObject, MISPAttribute

from core.logs import get_logger

logger = get_logger(__name__)


class MispToTrustar:
    def __init__(self, feed: list, *args, **kwargs) -> None:
        self.feed = feed

        self.allowed_tag_name_length = kwargs.get("allowed_tag_name_length", 20)

    def process_event(self, event: MISPEvent):
        report, attribute_tags = None, None
        try:
            report = Report(
                title=f"{event.info} - {event.id}",
                body=event.to_json(),
                time_began=event.date,
                external_id=event.uuid,
            )

            # Tags are fetched from 2 sources.
            # 1. Attribute Tags 2. Object Attribute Tags
            # 1. Get attributes tags
            attribute_tags = self.get_tags_from_attributes(event.Attribute)

            # 2. Get Object Attribute Tags
            # Iterate through objects of event to get attributes
            for objects in event.Object:
                # Append the tags from object attribute
                attribute_tags = attribute_tags.union(
                    self.get_tags_from_attributes(objects.Attribute)
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
            event = MISPEvent()
            event.from_json(item)
            report, tags = self.process_event(event)
            results.append({"report": report.to_dict(), "tags": tags})
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
            for tag in attributes.Tag:
                # Adding tags only if length of tag name <= 20.
                if len(tag.name) <= self.allowed_tag_name_length:
                    attribute_tags.add(tag.name)
                else:
                    logger.info(
                        "Ignoring Tag name {} of length {}".format(
                            tag.name, len(tag.name)
                        )
                    )

        return list(attribute_tags)


ENTITY_TYPE_MAPPINGS = {
    "BITCOIN_ADDRESS": "btc",
    "CIDR_BLOCK": "ip-src",
    "COMMENTS": "text",
    "CVE": "vulnerability",
    "EMAIL_ADDRESS": "email-src",
    "INDICATOR_SUMMARY": "text",
    "IP": "ip-src",
    "MALWARE": "malware-type",
    "MD5": "md5",
    "REGISTRY_KEY": "regkey",
    "REPORT_LINK": "link",
    "SHA1": "sha1",
    "SHA256": "sha256",
    "SOFTWARE": "filename",
    "URL": "url",
    "THREAT_ACTOR": "threat-actor",
}


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
                logger.info(f"Tranforming {element['report']['id']}")
                # Initialize and set MISPEvent()
                report = Report.from_dict(element["report"])
                tags = [Tag.from_dict(t) for t in element["tags"]] + [
                    Tag("TruSTAR"),
                    Tag("Report"),
                ]
                indicators = [Indicator.from_dict(i) for i in element["indicators"]]

                event = MISPEvent()
                try:
                    event.from_dict(
                        timestamp=report.created / 1000 if report.created else None,
                        info=f"TruSTAR Report: {report.title}",
                    )
                    event.date = event.timestamp.date()
                except Exception as e:
                    logger.warning(f"Failed parsing dates for report {report.id}")
                    logger.warning(e)
                    event.from_dict(
                        info=f"TruSTAR Report: {report.title}",
                    )
                logger.debug(f"Generating a MISP event for {event.info}")

                # Get tags for report
                for tag in tags:
                    event.add_tag(tag.name)
                    logger.debug(f"{tag.name} added to event")

                # Create MISP TruSTAR object to add indicators to event
                logger.debug(f"Adding deeplink ro {event.info}")
                event.add_attribute("link", element["deeplink"])

                # Get indicators for report
                logger.debug(f"Adding indicators to {event.info}")
                for indicator in indicators:
                    try:
                        attr = MISPAttribute()
                        try:
                            attr.from_dict(
                                value=indicator.value,
                                type=ENTITY_TYPE_MAPPINGS.get(indicator.type),
                                first_seen=indicator.first_seen / 1000
                                if indicator.first_seen
                                else None,
                                last_seen=indicator.last_seen / 1000
                                if indicator.last_seen
                                else None,
                            )
                        except Exception as e:
                            logger.warning(f"Failed parsing dates for IOC {indicator}")
                            logger.warning(e)
                            attr.from_dict(
                                value=indicator.value,
                                type=ENTITY_TYPE_MAPPINGS.get(indicator.type),
                            )

                        event.attributes.append(attr)
                    except Exception as ex:
                        logger.warning(
                            f"Failed to transform TruSTAR Indicator "
                            f"to MISP Attribute {ex}"
                        )

                events.append(event.to_json())
            except KeyError as k:
                logger.error(f"Missing {k}")
            except Exception as e:
                logger.error(
                    f"Failed to transform TruSTAR report {element['report'].id} "
                    f"to MISP event - {e}"
                )
        return events

    @staticmethod
    def iocs_to_misp_attributes(extacted_iocs: list):
        """
        Returns a MISPObject with the extracted IOCs as attributes
        """
        obj = MISPObject("trustar_report", standalone=False, strict=True)
        for indicator in extacted_iocs:
            try:
                obj.add_attribute(indicator.type, indicator.value)
            except Exception as ex:
                logger.error(f"Failed to transform IOC {indicator} with error {ex}")
        return obj.to_json()


def for_trustar_reports(extracted_data):
    transformer = MispToTrustar(extracted_data)
    processed_feed = transformer.process_feed()
    return processed_feed


def ts_reports_to_misp_event(extracted_data):
    result = TrustarToMisp.reports_to_misp_events(extracted_data)
    return result


def ts_enclave_ioc_to_misp_attributes(extracted_data: dict):
    try:
        transformed = []
        for data in extracted_data:
            transformed.append(
                {
                    "enclave": data["enclave"],
                    "iocs": TrustarToMisp.iocs_to_misp_attributes(data["iocs"]),
                }
            )
        return transformed
    except Exception as ex:
        logger.error("Failed to transform data")
        logger.exception(ex)
