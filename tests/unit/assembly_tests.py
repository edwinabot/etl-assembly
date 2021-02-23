import pytest


@pytest.mark.skip(reason="no way of currently testing this")
def test_job_creation_stage(dynamo):
    from core.assembly import job_creation_stage
    from core.etl import InMemoryQueue

    job_creation_stage(
        config_id="7f9010e3-f1b9-408a-8fbf-85fe20f8fd34", queue=InMemoryQueue()
    )


@pytest.mark.skip(reason="broken")
def test_extraction_stage(job):
    from core.assembly import extraction_stage
    from core.etl import InMemoryQueue, Extract, Transform

    extract_job = Extract.build(job=job)
    queue = InMemoryQueue(job_type=Transform)
    extraction_stage(extract_job=extract_job, queue=queue)
    transform_job = queue.get()  # type: Transform
    assert isinstance(transform_job, Transform)
    assert transform_job.extracted_data


@pytest.mark.skip(reason="broken")
def test_transformation_stage(job):
    from core.assembly import transformation_stage
    from core.etl import InMemoryQueue, Transform, Load

    transform = Transform(job, ["foo", "bar", "baz"])
    queue = InMemoryQueue(job_type=Load)
    transformation_stage(transform_job=transform, queue=queue)
    load_job = queue.get()  # type: Load
    assert isinstance(load_job, Load)
    assert load_job.transformed_data


def test_loading_stage(job):
    from core.assembly import loading_stage
    from core.etl import Load

    load = Load(job, ["foo", "bar", "baz"])
    loading_stage(load_job=load)
