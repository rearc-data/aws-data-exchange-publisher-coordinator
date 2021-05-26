import json
import boto3
import time
import calendar
import os
import sys
import logging
import traceback

from datetime import datetime


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

        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket, Key=key)
        manifest_dict_flat = json.loads(obj['Body'].read())

        product_id = manifest_dict_flat['product_id']
        dataset_id = manifest_dict_flat['dataset_id']
        asset_list = manifest_dict_flat['asset_list']
        num_assets = len(asset_list)

        if not product_id or not dataset_id or not asset_list:
            error_message = 'Invalid manifest file; missing required fields from manifest file: product_id, ' \
                            'dataset_id, asset_list '
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
        response = s3.put_object(Body=data, Bucket=bucket, Key=nested_manifest_file_key)

        EXECUTION_NAME = 'Execution-ADX-PublishingWorkflow-SFN@{}'.format(str(calendar.timegm(time.gmtime()))) 
        INPUT = json.dumps({
            "Bucket": bucket,
            "Key": nested_manifest_file_key
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
            "Version": os.getenv('Version'),
            "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "Bucket": bucket,
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

