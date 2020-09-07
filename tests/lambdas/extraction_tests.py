import pytest
from lambdas.extraction import lambda_handler


@pytest.mark.skip(reason="no way of currently testing this")
def test_perform_extraction_job():
    mock_event = {
        "Records": [
            {
                "messageId": "d84fdad6-5521-46b8-9c86-2b6e8f2ef46f",
                "receiptHandle": (
                    "AQEB4L/d9epeY/X60aFX8idNfz7xRv/ndd17EZo3RBwNxG3SFw"
                    "xAzjWmZ764Xq7CNbmBhbAMeLQaPcfu+xlxvwwORP55HW0V9wx0"
                    "gB6FfEVa11n55kG2WWLauA13y+UX4Y+tJb0nWUSKEdvvmoOztX"
                    "AcxhYXiV8wJm6w8Pemj3cQxllKhzSXYLlKXKHYkbI1i8Lop909"
                    "aOYrufUxfSYjuCD0RasS6RjbNmzKunFS4COzDtxu3m1/q0nS8c"
                    "cMX3sRrVAJHxA0S/bsOSNVznu5jFYue9n0gxyhByGgRd7iYlie"
                    "v0Xabx3JDKZoEVWNmifFefgt"
                ),
                "body": (
                    "gASVTgIAAAAAAACMCGNvcmUuZXRslIwHRXh0cmFjdJSTlCmBlH"
                    "2UKIwTX2NhbGxhYmxlX2FyZ3Vt\nZW50c5R9lIwDam9ilIwNY2"
                    "9yZS5yZWdpc3RyeZSMA0pvYpSTlCmBlH2UKIwDX2lklIwkN2Y5"
                    "MDEw\nZTMtZjFiOS00MDhhLThmYmYtODVmZTIwZjhmZDM0lIwJ"
                    "X3RlbXBsYXRllGgIjAhUZW1wbGF0ZZST\nlCmBlH2UKIwHZXh0"
                    "cmFjdJSMFHRlc3RpbmcuZG9fc29tZXRoaW5nlIwJdHJhbnNmb3"
                    "JtlIwedGVz\ndGluZy5kb19zb21lX3RyYW5zZm9ybWF0aW9ulI"
                    "wEbG9hZJSMFHRlc3RpbmcuZG9fc29tZXRoaW5n\nlIwCaWSUjC"
                    "Q1YjEzMmU5ZC00ZDg1LTQ4NDUtODA0YS1jNTRkZWIyYmFmYTaU"
                    "dWKMCl91c2VyX2Nv\nbmaUjCQyYTg3ZDlhYy1lMjQyLTQ1NGQt"
                    "OTQwNy1lNTYwMWNlYjA1MTmUjARuYW1llIwaVGVzdCBK\nT0Ig"
                    "dGhhdCBkb2VzIE5PVEhJTkeUjAtkZXNjcmlwdGlvbpSMAJSMCV"
                    "9sYXN0X3J1bpSMCGRhdGV0\naW1llIwIZGF0ZXRpbWWUk5RDCg"
                    "fkCBQSADYAvgWUaCOMCHRpbWV6b25llJOUaCOMCXRpbWVkZWx0"
                    "\nYZSTlEsASwBLAIeUUpSFlFKUhpRSlHVic4wNX2pvYl9jYWxs"
                    "YWJsZZSMFGNvcmUuY2F0YWxvZy50\nZXN0aW5nlIwMZG9fc29t"
                    "ZXRoaW5nlJOUaAdoC3ViLg==\n"
                ),
                "attributes": {
                    "ApproximateReceiveCount": "3",
                    "SentTimestamp": "1599259972031",
                    "SequenceNumber": "18856154626549487872",
                    "MessageGroupId": "assembly-messages",
                    "SenderId": "AROAUTMBT7OO7H33K3MCS:Staging-JobCreationFunction",
                    "MessageDeduplicationId": (
                        "e2d3d24df5bfb5066fff39c97869"
                        "2575a56c8e186a1a76d4fca2d52f0c1343ce"
                    ),
                    "ApproximateFirstReceiveTimestamp": "1599491029988",
                },
                "messageAttributes": {},
                "md5OfBody": "597e50fc157add1db4408bff72bb1129",
                "eventSource": "aws:sqs",
                "eventSourceARN": (
                    "arn:aws:sqs:us-east-2:316488809373:"
                    "Staging-ExtractJobsQueue.fifo"
                ),
                "awsRegion": "us-east-2",
            }
        ]
    }

    lambda_handler(mock_event, None)
