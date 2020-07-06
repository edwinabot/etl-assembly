import os
import logging

from logging.config import dictConfig

logging_config = dict(
    version=1,
    formatters={
        "f": {
            "format": (
                '{"time": "%(asctime)s",'
                '"module":"%(name)s",'
                '"level":"%(levelname)s",'
                '"message":"%(message)s"}'
            )
        }
    },
    handlers={
        "h": {
            "class": "logging.StreamHandler",
            "formatter": "f",
            "level": logging.DEBUG,
        }
    },
    root={"handlers": ["h"], "level": os.getenv("LOGLEVEL", default=logging.INFO)},
)

dictConfig(logging_config)


def get_logger(name=None):
    return logging.getLogger(name or __name__)
