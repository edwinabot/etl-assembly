import json

from dataclasses import dataclass

import boto3

import core.config as config
from core.logs import get_logger

logger = get_logger("database")


@dataclass
class TableDefinition:
    name: str
    attribute_deffinition: list
    provisioned_throughput: dict
    key_schema: list


def get_dynamo_connection(
    region=config.AWS_REGION, endpoint_url=config.DYNAMO_ENDPOINT
):
    try:
        logger.debug("Connecting to DynamoDB")
        dynamodb = boto3.resource("dynamodb", region, endpoint_url=endpoint_url)
        logger.debug("Connected to DynamoDB")
        return dynamodb
    except Exception as ex:
        logger.error(f"Failed to connect to DynamoDB {ex}")
        raise ex


def create_table(table_definition: TableDefinition):
    try:
        dynamodb = get_dynamo_connection()
        logger.debug(f"Creating {table_definition.name} table")
        table = dynamodb.create_table(
            TableName=table_definition.name,
            KeySchema=table_definition.key_schema,
            AttributeDefinitions=table_definition.attribute_deffinition,
            ProvisionedThroughput=table_definition.provisioned_throughput,
        )
        waiter = table.meta.client.get_waiter("table_exists")
        waiter.wait(TableName=table_definition.name)
        table = dynamodb.Table(table_definition.name)
        logger.debug(f"Table {table_definition.name} created")
        return table
    except Exception as ex:
        logger.error(f"Failed to create table {ex}")
        raise ex


def create_tables(tables: list):
    dynamodb = get_dynamo_connection()
    existing_tables = [t.name for t in dynamodb.tables.all()]
    if existing_tables:
        new_tables = [t for t in tables if t.name not in existing_tables]
    else:
        new_tables = tables
    for table in new_tables:
        create_table(table)


def get_table(table_definition: TableDefinition):
    dynamodb = get_dynamo_connection()
    try:
        logger.debug(f"Getting {table_definition.name} table")
        table = dynamodb.Table(table_definition.name)
        logger.debug(f"Got {table_definition.name} table")
        return table
    except Exception as ex:
        logger.error(f"Failed getting {table_definition.name} table {ex}")


def load_fixture_data(table_definition: TableDefinition, fixture: list):
    try:
        table = get_table(table_definition)
        logger.debug("Putting items")
        for item in fixture:
            table.put_item(Item=item)
        logger.debug("Items")
    except Exception as ex:
        logger.error(f"Unable to load fixture {ex}")


def load_fixtures(tables: list, fixture_path: str):
    for table in tables:
        try:
            with open(fixture_path, "r") as fixture_file:
                fixtures = json.load(fixture_file)
                load_fixture_data(table, fixtures[table.name])
        except FileNotFoundError:
            logger.error("Unable to locate fixture.json file")
            raise
        except Exception as ex:
            logger.error(ex)


TemplateTable = TableDefinition(
    "etl_assembly_templates",
    key_schema=[{"AttributeName": "id", "KeyType": "HASH"}],  # Partition key
    attribute_deffinition=[{"AttributeName": "id", "AttributeType": "S"}],
    provisioned_throughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
)

UserConfTable = TableDefinition(
    name="etl_assembly_user_configs",
    key_schema=[{"AttributeName": "id", "KeyType": "HASH"}],  # Partition key
    attribute_deffinition=[{"AttributeName": "id", "AttributeType": "S"}],
    provisioned_throughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
)

JobTable = TableDefinition(
    name="etl_assembly_jobs",
    key_schema=[{"AttributeName": "id", "KeyType": "HASH"}],  # Partition key
    attribute_deffinition=[{"AttributeName": "id", "AttributeType": "S"}],
    provisioned_throughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
)
