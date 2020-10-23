from datetime import datetime, timezone
import os

import pytest

from core.catalog.misp_automated.trustar.extraction import (
    StationExtractor,
    pull_reports,
)


def test_get_reports_30_days_time_window(trustar_extraction_job, mocker):
    from trustar.models import NumberedPage

    trustar_extraction_job.last_run = datetime(2020, 8, 1, 0, 0, 0, 0, timezone.utc)
    mocker.patch(
        "trustar.TruStar.search_reports_page",
        return_value=NumberedPage(
            items=[i for i in range(0, 100)],
            page_number=0,
            page_size=100,
            total_elements=50000,
            has_next=True,
        ),
    )
    mocker.patch(
        (
            "core.catalog.misp_automated.trustar"
            ".extraction.StationExtractor.get_current_datetime"
        ),
        return_value=datetime(2020, 8, 31, 23, 59, 59, 0, timezone.utc),
    )
    extractor = StationExtractor(trustar_extraction_job)
    reports = extractor.get_reports()
    assert len(reports) == 10000


def test_get_reports_30_minutes_time_window(trustar_extraction_job, mocker):
    from trustar.models import NumberedPage

    trustar_extraction_job.last_run = datetime(2020, 8, 31, 23, 10, 59, 0, timezone.utc)
    mocker.patch(
        "trustar.TruStar.search_reports_page",
        return_value=NumberedPage(
            items=[i for i in range(0, 24)],
            page_number=0,
            page_size=100,
            total_elements=24,
            has_next=False,
        ),
    )
    mocker.patch(
        (
            "core.catalog.misp_automated.trustar"
            ".extraction.StationExtractor.get_current_datetime"
        ),
        return_value=datetime(2020, 8, 31, 23, 40, 59, 0, timezone.utc),
    )
    extractor = StationExtractor(trustar_extraction_job)
    reports = extractor.get_reports()
    assert len(reports) == 24


def test_pull_reports(trustar_extraction_job, mocker):
    mocker.patch(
        (
            "core.catalog.misp_automated.trustar"
            ".extraction.StationExtractor.MAX_REPORT_COUNT"
        ),
        new=10,
    )
    results = pull_reports(trustar_extraction_job)
    assert len(results) <= 10


@pytest.fixture(scope="function")
def trustar_extraction_job(mocker, dynamo):
    from core.registry import Job, Template, UserConf

    mocker.patch(
        "core.registry.UserConf.source_secrets",
        new_callable=mocker.PropertyMock,
        return_value={
            "api_key": os.getenv("TRUSTAR_TEST_API_KEY", ""),
            "api_secret": os.getenv("TRUSTAR_TEST_API_SECRET", ""),
        },
    )
    mocker.patch(
        "core.registry.UserConf.destination_secrets",
        new_callable=mocker.PropertyMock,
        return_value={"secret": "destination"},
    )
    mocker.patch(
        "core.registry.Job.save",
        new_callable=mocker.MagicMock,
    )

    template = Template(
        "templateid",
        "testing.do_something",
        "testing.do_some_transformation",
        "testing.do_something",
    )

    user_conf = UserConf(
        "userconfid",
        source_conf={
            "auth": "https://staging.trustar.co/oauth/token",
            "base": "https://staging.trustar.co/api/1.3",
            "enclave_ids": [
                "f7823953-6324-4710-96cd-7c4d0e1a9e28",
                "2792f66d-7764-4d5d-b6f1-84800c923feb",
            ],
            "frequency": "rate(5 minutes)",
            "client_metatag": "Edwin's ETL Assembly POC",
            "report_deeplink_base": "https://staging.trustar.co/constellation/reports/",
        },
        destination_conf={},
        trustar_user_id="edwinstrustarid",
        created_at="2020-06-01T17:30:00Z",
        updated_at="2020-06-01T17:30:00Z",
    )
    job = Job(
        template=template,
        user_conf=user_conf,
        last_run="2020-01-01T18:00:54.048645+00:00",
        name="Mock Job",
        _id="jobid",
        description="This is the description for a mock job.",
    )

    return job
