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


def handle_insert(record, events, lambdas):
    handler = DynamoInsertHandler()
    handler(record, events, lambdas)


def handle_modify(record, events, lambdas):
    handle_insert(record, events, lambdas)


def get_rule_name(job_id: str):
    return f"etl_assembly_job_{job_id}"


def handle_remove(record, events, lambdas):
    handler = DynamoRemoveHandler()
    handler(record, events, lambdas)


class DynamoInsertHandler:
    def __call__(self, record, events, lambdas):
        self.events = events
        self.lambdas = lambdas
        self.job = None
        try:
            self.job = Job.get(record["dynamodb"]["Keys"]["id"]["S"])  # type: Job
        except Exception as e:
            logger.warning(e)
            return
        rule_name = get_rule_name(self.job.id)
        rule_response = self.put_eventbridge_rule(rule_name)
        self.put_rule_targets(rule_name)
        self.grant_lambda_permissions(rule_response)
        logger.info(f"EventBridge Rule Put for Job {self.job.id}: {self.job.name}")

    def put_eventbridge_rule(self, rule_name):
        rule_response = self.events.put_rule(
            Name=rule_name,
            ScheduleExpression=self.job.user_conf.source_conf["frequency"],
            State="ENABLED",
            Description=(f"ETL-Assembly Rule Job ID: {self.job.id} {self.job.name}"),
        )
        logger.debug(rule_response)
        return rule_response

    def put_rule_targets(self, rule_name):
        target_response = self.events.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    "Arn": config.JOB_CREATION_FUNCTION_ARN,
                    "Id": config.JOB_CREATION_FUNCTION,
                    "Input": json.dumps({"config_id": self.job.id}),
                }
            ],
        )
        logger.debug(target_response)
        return target_response

    def grant_lambda_permissions(self, rule_response):
        try:
            self.lambdas.add_permission(
                FunctionName=config.JOB_CREATION_FUNCTION,
                StatementId=get_rule_name(self.job.id),
                Action="lambda:InvokeFunction",
                Principal="events.amazonaws.com",
                SourceArn=rule_response["RuleArn"],
            )
            logger.info(
                f"InvokeFunction action granted to Rule {get_rule_name(self.job.id)}"
            )
        except botocore.exceptions.ClientError as error:
            # https://boto3.amazonaws.com/v1/documentation/
            # api/latest/guide/error-handling.html
            # #parsing-error-responses-and-catching-exceptions-from-aws-services
            logger.debug(error)
            logger.info(
                (
                    "InvokeFunction action already granted to Rule "
                    f"{get_rule_name(self.job.id)}"
                )
            )


class DynamoRemoveHandler:
    def __call__(self, record, events, lambdas):
        conf_id = record["dynamodb"]["Keys"]["id"]["S"]
        logger.debug(f"Removing cronjob for deleted configuration {conf_id}")
        self.events = events
        self.lambdas = lambdas
        rule_name = get_rule_name(conf_id)
        self.revoke_lambda_permissions(conf_id, rule_name)
        logger.info(f"Removed EventBridge rule for deleted Job id:{conf_id}")

    def revoke_lambda_permissions(self, conf_id, rule_name):
        self.lambdas.remove_permission(
            FunctionName=config.JOB_CREATION_FUNCTION, StatementId=rule_name,
        )

    def remove_rule_targets(self, rule_name):
        targets_response = self.events.remove_targets(
            Rule=rule_name, Ids=[config.JOB_CREATION_FUNCTION]
        )
        logger.debug(targets_response)

    def delete_eventbridge_rule(self, rule_name):
        self.events.delete_rule(Name=rule_name)
