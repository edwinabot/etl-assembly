import json

import boto3
import botocore

from enum import Enum

from core import config
from core.logs import get_logger
from core.registry import Job


logger = get_logger(__name__)


class DynamoEvent(Enum):
    INSERT = "INSERT"
    MODIFY = "MODIFY"
    REMOVE = "REMOVE"


def lambda_handler(event, context):
    # Build a job object
    logger.debug(f"Handling event {event}")
    logger.debug(context)
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html
    events = boto3.client("events")
    lambdas = boto3.client("lambda")
    handlers = {
        DynamoEvent.INSERT.value: handle_insert,
        DynamoEvent.MODIFY.value: handle_modify,
        DynamoEvent.REMOVE.value: handle_remove,
    }
    for record in event.get("Records", []):
        handlers[record["eventName"]](record, events, lambdas)


def get_rule_name(job_id: str):
    return f"etl_assembly_job_{job_id}"


def handle_insert(record, client, lambdas):
    job = Job.get(record["dynamodb"]["Keys"]["id"]["S"])  # type: Job
    rule_response = client.put_rule(
        Name=get_rule_name(job.id),
        ScheduleExpression=job.user_conf.source_conf["frequency"],
        State="ENABLED",
        Description=f"ETL-Assembly Rule Job ID: {job.id} {job.description}",
    )
    logger.debug(rule_response)
    target_response = client.put_targets(
        Rule=get_rule_name(job.id),
        Targets=[
            {
                "Arn": config.JOB_CREATION_FUNCTION_ARN,
                "Id": config.JOB_CREATION_FUNCTION,
                "Input": json.dumps({"config_id": job.id}),
            }
        ],
    )
    logger.debug(target_response)
    try:
        lambdas.add_permission(
            FunctionName=config.JOB_CREATION_FUNCTION,
            StatementId=get_rule_name(job.id),
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=rule_response["RuleArn"],
        )
        logger.info(f"InvokeFunction action granted to Rule {get_rule_name(job.id)}")
    except botocore.exceptions.ClientError as error:
        # https://boto3.amazonaws.com/v1/documentation/
        # api/latest/guide/error-handling.html
        # #parsing-error-responses-and-catching-exceptions-from-aws-services
        logger.debug(error)
        logger.info(
            f"InvokeFunction action already granted to Rule {get_rule_name(job.id)}"
        )

    logger.info(f"EventBridge Rule Put for Job {job.id}: {job.name}")


def handle_modify(record, client, lambdas):
    handle_insert(record, client, lambdas)


def handle_remove(record, client, lambdas):
    conf_id = record["dynamodb"]["Keys"]["id"]["S"]
    logger.debug(f"Removing cronjob for deleted configuration {conf_id}")
    lambdas.remove_permission(
        FunctionName=config.JOB_CREATION_FUNCTION, StatementId=get_rule_name(conf_id)
    )
    targets_response = client.remove_targets(
        Rule=get_rule_name(conf_id), Ids=[config.JOB_CREATION_FUNCTION,],
    )
    logger.debug(targets_response)
    client.delete_rule(Name=get_rule_name(conf_id))
    logger.info(f"Removed EventBridge rule for deleted Job id:{conf_id}")
