import pytest

# import boto3
import os

from moto import mock_dynamodb2

import config


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="function")
def dynamo(aws_credentials):
    with mock_dynamodb2():
        from database import (
            create_tables,
            load_fixtures,
            UserConfTable,
            JobTable,
            TemplateTable,
        )

        tables = [TemplateTable, JobTable, UserConfTable]
        create_tables(tables)
        load_fixtures(tables, config.FIXTURE_PATH)
        yield
