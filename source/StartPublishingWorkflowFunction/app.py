import json
import boto3
import time
import calendar
import os
import sys
import logging
from datetime import datetime
import random
import traceback

def lambda_handler(event, context):
    """
    This function triggers from an S3 event source when a manifest file
    for a new product update is put in the ManifestBucket
    """
    
    try:
        global log_level
        log_level = str(os.environ.get('LOG_LEVEL')).upper()
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_log_levels:
            log_level = 'ERROR'

        logging.getLogger().setLevel(log_level)
 
        STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']
        logging.debug('event={}'.format(event))
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        logging.info('validating the manifest file from s3://{}/{}'.format(bucket, key))

        product_id = s3_select(bucket, key, """SELECT * FROM s3object[*].product_id r;""")
        dataset_id = s3_select(bucket, key, """SELECT * FROM s3object[*].dataset_id r;""")
        asset_list = s3_select(bucket, key, """SELECT * FROM s3object[*].asset_list r;""")
        num_assets = len(asset_list)

        if not product_id or not dataset_id or not asset_list:
            error_message = 'Invalid manifest file; missing required fields from manifest file: product_id, dataset_id, asset_list'
            logging.error(error_message)
            sys.exit(error_message)

        logging.debug("bucket: {}\nkey: {}\nproduct_id: {}\ndatset_id: {}\nnum_assets:{}".format(bucket, key, product_id, dataset_id, num_assets))

        asset_list_nested = []

        logging.info('chunck into lists of 10k assets to account for ADX limit of 10k assets per revision')
        asset_lists_10k = [asset_list[i:i+10000] for i in range(0, len(asset_list), 10000)]

        for revision_index, assets_10k in enumerate(asset_lists_10k):
            logging.info('chunck into lists of 100 assets to account for ADX limit of 100 assets per job')
            asset_lists_100 = [assets_10k[i:i+100] for i in range(0, len(assets_10k), 100)]
            asset_list_nested.append(asset_lists_100)

        nested_manifest_file_key = key.split('.')[0] + '.manifest'

        manifest_dict = {
            'product_id': product_id,
            'dataset_id': dataset_id,
            'asset_list_nested': asset_list_nested
        }

        s3 = boto3.client('s3')
        data = json.dumps(manifest_dict).encode('utf-8')
        response = s3.put_object(Body=data, Bucket=bucket,Key=nested_manifest_file_key)

        EXECUTION_NAME = 'Execution-ADX-PublishingWorkflow-SFN@{}'.format(str(calendar.timegm(time.gmtime()))) 
        INPUT = json.dumps({
            "Bucket" : bucket,
            "Key" : nested_manifest_file_key
        })
        sfn = boto3.client('stepfunctions')
        logging.debug('EXECUTION_NAME={}'.format(EXECUTION_NAME))
        response = sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=EXECUTION_NAME,
            input=INPUT
        )
        logging.debug('INPUT={}'.format(INPUT))
        logging.debug('sf response={}'.format(response))

        metrics = {
            "Version" : os.getenv('Version'),
            "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "Bucket" : bucket,
            "Key": nested_manifest_file_key,
            "StateMachineARN" : STATE_MACHINE_ARN,
            "ExecutionName": EXECUTION_NAME
        }
        logging.info('Metrics:{}'.format(metrics))

    except Exception as error:
        logging.error('lambda_handler error: %s' % (error))
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        result = {
            'Error': 'error={}'.format(error)
        }
        return json.dumps(result)
    return {
        "Message": "State machine started"
    }


def s3_select(bucket, key, sql_expression):
    """Select data from an object on S3"""
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
        logging.debug(event)
        if "Records" in event and "Payload" in event["Records"]:
            try:
                result = json.loads(event["Records"]["Payload"].decode("utf-8"))["_1"]
                logging.debug("result: {}".format(result))
                logging.debug(type(result))
            except Exception as e:
                logging.debug('ERROR')
                logging.debug(e)
            
    return result
