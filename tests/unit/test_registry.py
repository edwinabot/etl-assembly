import pytest

from registry import JobConfig


def test_non_existant_job_configuration():
    with pytest.raises(ValueError):
        JobConfig.get(_id="this does not exists")
