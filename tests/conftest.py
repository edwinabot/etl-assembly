import pytest

import os

from moto import mock_dynamodb2

import core.config as config


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
        from core.database import (
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


@pytest.fixture(scope="function")
def job(mocker, dynamo):
    from core.registry import Job, Template, UserConf

    mocker.patch(
        "core.registry.UserConf.source_secrets",
        new_callable=mocker.PropertyMock,
        return_value={"secret": "source"},
    )
    mocker.patch(
        "core.registry.UserConf.destination_secrets",
        new_callable=mocker.PropertyMock,
        return_value={"secret": "destination"},
    )
    mocker.patch(
        "core.registry.Job.save", new_callable=mocker.MagicMock,
    )

    template = Template(
        "templateid",
        "testing.do_something",
        "testing.do_some_transformation",
        "testing.do_something",
    )

    user_conf = UserConf(
        "userconfid",
        source_conf={},
        destination_conf={},
        trustar_user_id="edwinstrustarid",
        created_at="2020-06-01T17:30:00Z",
        updated_at="2020-06-01T17:30:00Z",
    )
    job = Job(
        template=template,
        user_conf=user_conf,
        last_run="2020-08-20T18:00:54.048645+00:00",
        name="Mock Job",
        _id="jobid",
        description="This is the description for a mock job.",
    )

    return job
