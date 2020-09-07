import logging

from logging.config import dictConfig

from core import config

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
    root={"handlers": ["h"], "level": config.LOGLEVEL},
)

dictConfig(logging_config)


def get_logger(name=None):
    return logging.getLogger(name or __name__)
