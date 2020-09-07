from core import config
from core.etl import SqsQueue, Extract
from core.assembly import extraction_stage
from core.logs import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.debug(event)
    logger.debug(context)
    serialized_job = event["body"]
    job = Extract.deserialize(serialized_job)
    transformation_queue = SqsQueue(queue_url=config.TRANSFORM_JOBS_QUEUE)
    extraction_stage(job, transformation_queue)


# foo = {
#     "Records": [
#         {
#             "messageId": "d84fdad6-5521-46b8-9c86-2b6e8f2ef46f",
#             "receiptHandle": "AQEB4L/d9epeY/X60aFX8idNfz7xRv/ndd17EZo3RBwNxG3SFwxAzjWmZ764Xq7CNbmBhbAMeLQaPcfu+xlxvwwORP55HW0V9wx0gB6FfEVa11n55kG2WWLauA13y+UX4Y+tJb0nWUSKEdvvmoOztXAcxhYXiV8wJm6w8Pemj3cQxllKhzSXYLlKXKHYkbI1i8Lop909aOYrufUxfSYjuCD0RasS6RjbNmzKunFS4COzDtxu3m1/q0nS8ccMX3sRrVAJHxA0S/bsOSNVznu5jFYue9n0gxyhByGgRd7iYliev0Xabx3JDKZoEVWNmifFefgt",
#             "body": "gASVTgIAAAAAAACMCGNvcmUuZXRslIwHRXh0cmFjdJSTlCmBlH2UKIwTX2NhbGxhYmxlX2FyZ3Vt\nZW50c5R9lIwDam9ilIwNY29yZS5yZWdpc3RyeZSMA0pvYpSTlCmBlH2UKIwDX2lklIwkN2Y5MDEw\nZTMtZjFiOS00MDhhLThmYmYtODVmZTIwZjhmZDM0lIwJX3RlbXBsYXRllGgIjAhUZW1wbGF0ZZST\nlCmBlH2UKIwHZXh0cmFjdJSMFHRlc3RpbmcuZG9fc29tZXRoaW5nlIwJdHJhbnNmb3JtlIwedGVz\ndGluZy5kb19zb21lX3RyYW5zZm9ybWF0aW9ulIwEbG9hZJSMFHRlc3RpbmcuZG9fc29tZXRoaW5n\nlIwCaWSUjCQ1YjEzMmU5ZC00ZDg1LTQ4NDUtODA0YS1jNTRkZWIyYmFmYTaUdWKMCl91c2VyX2Nv\nbmaUjCQyYTg3ZDlhYy1lMjQyLTQ1NGQtOTQwNy1lNTYwMWNlYjA1MTmUjARuYW1llIwaVGVzdCBK\nT0IgdGhhdCBkb2VzIE5PVEhJTkeUjAtkZXNjcmlwdGlvbpSMAJSMCV9sYXN0X3J1bpSMCGRhdGV0\naW1llIwIZGF0ZXRpbWWUk5RDCgfkCBQSADYAvgWUaCOMCHRpbWV6b25llJOUaCOMCXRpbWVkZWx0\nYZSTlEsASwBLAIeUUpSFlFKUhpRSlHVic4wNX2pvYl9jYWxsYWJsZZSMFGNvcmUuY2F0YWxvZy50\nZXN0aW5nlIwMZG9fc29tZXRoaW5nlJOUaAdoC3ViLg==\n",
#             "attributes": {
#                 "ApproximateReceiveCount": "3",
#                 "SentTimestamp": "1599259972031",
#                 "SequenceNumber": "18856154626549487872",
#                 "MessageGroupId": "assembly-messages",
#                 "SenderId": "AROAUTMBT7OO7H33K3MCS:Staging-JobCreationFunction",
#                 "MessageDeduplicationId": "e2d3d24df5bfb5066fff39c978692575a56c8e186a1a76d4fca2d52f0c1343ce",
#                 "ApproximateFirstReceiveTimestamp": "1599491029988",
#             },
#             "messageAttributes": {},
#             "md5OfBody": "597e50fc157add1db4408bff72bb1129",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:us-east-2:316488809373:Staging-ExtractJobsQueue.fifo",
#             "awsRegion": "us-east-2",
#         }
#     ]
# }
