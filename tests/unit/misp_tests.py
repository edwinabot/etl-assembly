def test_pull_feeds(dynamo):
    from registry import Job
    from etl import Extract

    jobconf = Job.get(_id="7f9010e3-f1b9-408a-8fbf-85fe20f8fd34")
    job = Extract(jobconf)
    job.run()
