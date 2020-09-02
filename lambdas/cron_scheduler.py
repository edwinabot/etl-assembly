import json
import boto3

from enum import Enum

from core import config
from core.logs import get_logger
from core.registry import Job


logger = get_logger(__name__)


class DynamoEvent(Enum):
    INSERT = "INSERT"
    MODIFY = "MODIFY"
    REMOVE = "REMOVE"


def handle_insert(record, client):
    job = Job.get(record["dynamodb"]["Keys"]["id"]["S"])  # type: Job
    rule_response = client.put_rule(
        Name=f"etl_assembly_job_id_{job.id}",
        ScheduleExpression=job.user_conf.source_conf["frequency"],
        State="ENABLED",
        Description=job.description,
    )
    logger.debug(rule_response)
    exploded_arn = rule_response["RuleArn"].split(":")
    job_creation_function_arn = (
        f"arn:aws:lambda:{exploded_arn[3]}:{exploded_arn[4]}"
        f":function:{config.JOB_CREATION_FUNCTION}"
    )
    target_response = client.put_targets(
        Rule=f"etl_assembly_job_id_{job.id}",
        Targets=[
            {
                "Arn": job_creation_function_arn,
                "Id": config.JOB_CREATION_FUNCTION,
                "Input": json.dumps({"config_id": job.id}),
            }
        ],
    )
    logger.debug(target_response)
    logger.info(f"EventBridge Rule created for Job {job.id}: {job.name}")


def handle_modify(record, client):
    handle_insert(record, client)


def handle_remove(record, client):
    conf_id = record["dynamodb"]["Keys"]["id"]["S"]
    logger.debug(f"Removing cronjob for deleted configuration {conf_id}")
    targets_response = client.remove_targets(
        Rule=f"etl_assembly_job_id_{conf_id}",
        Ids=[
            config.JOB_CREATION_FUNCTION,
        ],
    )
    logger.debug(targets_response)
    client.delete_rule(Name=f"etl_assembly_job_id_{conf_id}")
    logger.info(f"Removed EventBridge rule for deleted Job id:{conf_id}")


def lambda_handler(event, context):
    # Build a job object
    logger.debug(f"Handling event {event}")
    logger.debug(context)
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html
    events = boto3.client("events")
    handlers = {
        DynamoEvent.INSERT.value: handle_insert,
        DynamoEvent.MODIFY.value: handle_modify,
        DynamoEvent.REMOVE.value: handle_remove,
    }
    for record in event.get("Records", []):
        handlers[record["eventName"]](record, events)
