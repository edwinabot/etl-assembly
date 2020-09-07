import pytest
from lambdas.cron_scheduler import lambda_handler


@pytest.mark.skip(reason="no way of currently testing this")
def test_remove_dynamo_event():
    mock_event = {
        "Records": [
            {
                "eventID": "e32e9bf744530c8ca8dce3793c4ab4ac",
                "eventName": "REMOVE",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "us-east-1",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1598989861.0,
                    "Keys": {"id": {"S": "6c7e83fd-9c22-45ff-829d-59c887917c6f"}},
                    "SequenceNumber": "200000000000876295022",
                    "SizeBytes": 38,
                    "StreamViewType": "KEYS_ONLY",
                },
                "eventSourceARN": (
                    "arn:aws:dynamodb:us-east-1:316488809373:table/"
                    "Staging-etl-assembly-jobs/stream/2020-09-01T18:36:49.639"
                ),
            }
        ]
    }
    lambda_handler(mock_event, None)


@pytest.mark.skip(reason="no way of currently testing this")
def test_insert_dynamo_event():
    mock_event = {
        "Records": [
            {
                "eventID": "4b5c6f051bd5bc4297a1c886c0f0f683",
                "eventName": "INSERT",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "us-east-1",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1598989896.0,
                    "Keys": {"id": {"S": "6c7e83fd-9c22-45ff-829d-59c887917c6f"}},
                    "SequenceNumber": "600000000032819717178",
                    "SizeBytes": 38,
                    "StreamViewType": "KEYS_ONLY",
                },
                "eventSourceARN": (
                    "arn:aws:dynamodb:us-east-1:316488809373:table/"
                    "Staging-etl-assembly-jobs/stream/2020-09-01T18:36:49.639"
                ),
            }
        ]
    }

    lambda_handler(mock_event, None)


@pytest.mark.skip(reason="no way of currently testing this")
def test_modify_dynamo_event():
    mock_event = {
        "Records": [
            {
                "eventID": "e43b7586e2459674d4ca5aed5a01e463",
                "eventName": "MODIFY",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "us-east-1",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1598990534.0,
                    "Keys": {"id": {"S": "cbac3537-1917-446c-9232-8a027ad99139"}},
                    "SequenceNumber": "700000000032820118610",
                    "SizeBytes": 38,
                    "StreamViewType": "KEYS_ONLY",
                },
                "eventSourceARN": (
                    "arn:aws:dynamodb:us-east-1:316488809373:table/"
                    "Staging-etl-assembly-jobs/stream/2020-09-01T18:36:49.639"
                ),
            }
        ]
    }

    lambda_handler(mock_event, None)
    assert False
