from typing import Union

import requests

from core.etl import Extract, Transform, Load
from core.logs import get_logger

logger = get_logger(__name__)


def do_something(job: Union[Extract, Transform, Load]):
    logger.info(f"Performed {job.__class__.__name__}")
    return [{"foo": 1, "bar": 2}]


def do_some_extraction(job: Union[Extract, Transform, Load]):
    result = do_something(job)
    response = requests.get("https://www.trustar.co/")
    response.raise_for_status()
    return result


def do_some_loading(job: Union[Extract, Transform, Load]):
    result = do_something(job)
    response = requests.get("https://www.trustar.co/")
    response.raise_for_status()
    return result


def do_some_transformation(extracted_data):
    logger.info(f"Performed Transformation on {extracted_data}")
    return extracted_data
