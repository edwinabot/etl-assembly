from datetime import datetime, timedelta, timezone

import pytest
from trustar.models.numbered_page import NumberedPage

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


@pytest.mark.skip(reason="Not a unit test, hist the prod/staging api")
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


def test_pull_reports_with_timewindow(trustar_extraction_job, mocker):
    to = datetime(2020, 10, 30, 23, 59, 59, 0, timezone.utc)
    since = to - timedelta(minutes=15)
    trustar_extraction_job.user_conf.source_conf["timewindow"] = {
        "from": since,
        "to": to,
    }
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
    extractor = StationExtractor(trustar_extraction_job)
    reports = extractor.get_reports()
    assert len(reports) <= StationExtractor.MAX_REPORT_COUNT
