import boto3
import os
import logging
import json

from datetime import datetime


def lambda_handler(event, context):
    """
    This function creates a new import job for the dataset revision 
    and starts the job to add it to AWS Data Exchange
    """
    try:
        global log_level
        log_level = str(os.getenv('LOG_LEVEL')).upper()
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_log_levels:
            log_level = 'ERROR'

        logging.getLogger().setLevel(log_level)

        logging.debug(f'{event=}')

        dataexchange = boto3.client(service_name='dataexchange')

        bucket = event['Bucket'] 
        key = event['Key']
        product_id = event['ProductId']
        dataset_id = event['DatasetId']
        revision_id = event['RevisionId']
        revision_index = event['RevisionMapIndex']
        job_index = event['JobMapIndex']

        logging.debug(f"{bucket=}\n{key=}\n{product_id=}\n{dataset_id=}\n{revision_index=}\n{job_index=}")
        logging.info("Creating and starting and import job")
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket, Key=key)
        manifest_dict = json.loads(obj['Body'].read())
        job_assets = manifest_dict['asset_list_nested'][revision_index][job_index]
        num_job_assets = len(job_assets)

        logging.debug(f"Job Assets from manifest file: {job_assets=}")
        logging.info(f"Total Job Assets: {num_job_assets}")

        revision_details = {
            "ImportAssetsFromS3": {
                "AssetSources": job_assets,
                "DataSetId": dataset_id,
                "RevisionId": revision_id
            }
        }
        logging.debug(f'{revision_details=}')

        create_job_response = dataexchange.create_job(Type='IMPORT_ASSETS_FROM_S3', Details=revision_details)
        job_arn = create_job_response['Arn']
        job_id = job_arn.split('/')[1]

        logging.info(f'{job_id=}')
          
        start_job_response = dataexchange.start_job(JobId=job_id)
        http_response = start_job_response['ResponseMetadata']['HTTPStatusCode']
        logging.debug(f'HTTPResponse={http_response}')

        get_job_response = dataexchange.get_job(JobId=job_id)  
        logging.debug(f'get job = {get_job_response}')
        job_status = get_job_response['State']
        
        metrics = {
            "Version": os.getenv('Version'),
            "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "ProductId": product_id,
            "DatasetId": dataset_id,
            "RevisionId": revision_id,
            "JobId": job_id,
            "RevisionMapIndex": revision_index,
            "JobMapIndex": job_index
        }
        logging.info(f'Metrics:{metrics}')

    except Exception as e:
        logging.error(e)
        raise e

    return {
        "StatusCode": 200,
        "Message": f"New import job created for RevisionId: {revision_id} JobId: {job_id} and started for {num_job_assets} assets",
        "ProductId": product_id,
        "DatasetId": dataset_id,
        "RevisionId": revision_id,
        "RevisionMapIndex": revision_index,
        "JobMapIndex": job_index,
        "JobId": job_id,
        "JobStatus": job_status,
        "JobAssetCount": num_job_assets
    }
