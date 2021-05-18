import json
import boto3
import os
import logging
from datetime import datetime
import urllib3
import random


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
        
        logging.debug('event={}'.format(event))

        dataexchange = boto3.client(service_name='dataexchange')
        s3 = boto3.client(service_name='s3') 

        bucket = event['Bucket'] 
        key = event['Key']
        product_id = event['ProductId']
        dataset_id = event['DatasetId']
        revision_id = event['RevisionId']
        revision_index = event['RevisionMapIndex']
        job_index = event['JobMapIndex']

        logging.debug("bucket: {}\nkey: {}\nproduct_id: {}\ndatset_id: {}\nrevision_index: {}\njob_index: {}".format(bucket, key, product_id, dataset_id, revision_index, job_index))

        logging.info("Creating and starting and import job")
        select_expression = """SELECT * FROM s3object[*].asset_list_nested[{}][{}] r;""".format(revision_index, job_index)
        job_assets = s3_select(bucket, key, select_expression)
        num_job_assets = len(job_assets)

        logging.debug("job_assets: {}".format(job_assets))
        logging.info("Total Job Assets: {}".format(num_job_assets))

        revision_details = {
            "ImportAssetsFromS3": {
                "AssetSources": job_assets,
                "DataSetId": dataset_id,
                "RevisionId": revision_id
            }
        }
        logging.debug('revision details = {}'.format(revision_details))

        create_job_response = dataexchange.create_job(Type='IMPORT_ASSETS_FROM_S3', Details=revision_details)
        job_arn = create_job_response['Arn']
        job_id = job_arn.split('/')[1]

        logging.info('jobId={}'.format(job_id))
          
        start_job_response = dataexchange.start_job(JobId=job_id)
        http_response = start_job_response['ResponseMetadata']['HTTPStatusCode']
        logging.debug('HTTPResponse={}'.format(http_response))

        get_job_response = dataexchange.get_job(JobId=job_id)  
        logging.debug('get job = {}'.format(get_job_response))
        job_status = get_job_response['State']
        
        metrics = {
            "Version" : os.getenv('Version'),
            "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "ProductId" : product_id,
            "DatasetId": dataset_id,
            "RevisionId": revision_id,
            "JobId": job_id,
            "RevisionMapIndex": revision_index,
            "JobMapIndex": job_index
        }
        logging.info('Metrics:{}'.format(metrics))


    except Exception as e:
       logging.error(e)
       raise e
    return {
        "StatusCode": 200,
        "Message": "New import job created for RevisionId: {} JobId: {} and started for {} assets".format(revision_id, job_id, num_job_assets),
        "ProductId" : product_id,
        "DatasetId": dataset_id,
        "RevisionId": revision_id,
        "RevisionMapIndex": revision_index,
        "JobMapIndex": job_index,
        "JobId": job_id,
        "JobStatus" : job_status,
        "JobAssetCount": num_job_assets
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
                logging.debug('ERROR:::')
                logging.debug(e)
            
    return result
