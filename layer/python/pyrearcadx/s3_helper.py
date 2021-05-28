import boto3
import logging
import json

from typing import Any

logger = logging.getLogger(__name__)


def s3_select(bucket: str, key: str, sql_expression: str) -> Any:
    """ Select data from an object on S3 object based on a sql_expression """
    client = boto3.client("s3")
    expression_type = "SQL"
    input_serialization = {"JSON": {"Type": "Document"}}
    output_serialization = {"JSON": {}}
    response = client.select_object_content(
        Bucket=bucket,
        Key=key,
        ExpressionType=expression_type,
        Expression=sql_expression,
        InputSerialization=input_serialization,
        OutputSerialization=output_serialization
    )

    result = None
    for event in response["Payload"]:
        logger.debug(event)
        if "Records" in event and "Payload" in event["Records"]:
            try:
                result = json.loads(event["Records"]["Payload"].decode("utf-8"))["_1"]
                logger.debug("result: {}".format(result))
                logger.debug(type(result))
            except Exception as e:
                logger.debug('ERROR:::')
                logger.debug(e)

    return result
