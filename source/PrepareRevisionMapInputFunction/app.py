import boto3
import os
import logging
import json

from datetime import datetime


def lambda_handler(event, context):
    """
    This function prepares input for the revision map state
    """
    try:
        global log_level
        log_level = str(os.getenv('LOG_LEVEL')).upper()
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_log_levels:
            log_level = 'ERROR'

        logging.getLogger().setLevel(log_level)
        
        logging.debug(f'{event=}')

        bucket = event['Bucket'] 
        key = event['Key']
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket, Key=key)
        manifest_dict = json.loads(obj['Body'].read())

        product_id = manifest_dict['product_id']
        dataset_id = manifest_dict['dataset_id']

        logging.debug(f"{bucket=}\n{key=}\n{product_id=}\n{dataset_id=}")

        num_revisions = len(manifest_dict['asset_list_nested'])

        num_jobs = 0
        num_revision_assets = 0
        if num_revisions:
            logging.info(f"Creating the input list to create {num_revisions} revisions")
            revision_map_input_list = list(range(num_revisions))

            for revisions_index in range(num_revisions):
                num_revision_assets = len(manifest_dict['asset_list_nested'][revisions_index])
                num_jobs += num_revision_assets

            metrics = {
                "Version": os.getenv('Version'),
                "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
                "ProductId": product_id,
                "DatasetId": dataset_id,
                "RevisionAssetCount": num_revision_assets,
                "TotalJobCount": num_jobs,
                "RevisionMapInput": revision_map_input_list
            }
            logging.info(f'Metrics:{metrics}')

    except Exception as e:
        logging.error(e)
        raise e

    return {
        "StatusCode": 200,
        "Message": "Input generated for {} revisions and {} jobs".format(num_revisions, num_jobs),
        "Bucket": bucket,
        "Key": key,
        "ProductId": product_id,
        "DatasetId": dataset_id,
        "RevisionCount": num_revisions,
        "TotalJobCount": num_jobs,
        "RevisionMapInput": revision_map_input_list
    }
