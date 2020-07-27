import pytest

from registry import Job


def test_non_existant_job_configuration(dynamo):
    with pytest.raises(ValueError):
        Job.get(_id="this does not exists")
