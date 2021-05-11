import json
import boto3
import os
import logging
from datetime import datetime
import urllib3
import random

def lambda_handler(event, context):
    """This function checks and returns the import assets job status"""
    try:
        global log_level
        log_level = str(os.environ.get('LOG_LEVEL')).upper()
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_log_levels:
            log_level = 'ERROR'

        logging.getLogger().setLevel(log_level)

        logging.debug('event={}'.format(event))

        dataexchange = boto3.client(service_name='dataexchange')
        s3 = boto3.client(service_name='s3') 

        product_id = event['ProductId']
        dataset_id = event['DatasetId']
        revision_id = event['RevisionId']
        job_id = event['JobId']
        # revision_index = event['RevisionMapIndex']
        # job_index = event['JobMapIndex']
        
        job_response = dataexchange.get_job(JobId=job_id) 
        logging.debug('get job = {}'.format(job_response))

        job_status = job_response['State']

        send_metrics = os.getenv('AnonymousUsage')
        if send_metrics == "Yes":
            kpis = {
                "Version" : os.getenv('Version'),
                "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
                "ProductId" : product_id,
                "DatasetId": dataset_id,
                "RevisionId": revision_id
                # "RevisionMapIndex": revision_index,
                # "JobMapIndex": job_index
            }
            # metric_data={
            #     "Solution": os.getenv('SolutionId'),
            #     "UUID": os.getenv('UUID'),
            #     "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            #     "Data": kpis
            # }
            
            # resp = send_metrics_rest_api(metric_data)
            # logging.debug('Send metrics to REST API endpoint response:{}'.format(resp))

            logging.info('Sending CloudWatch custom metric:{}'.format(kpis))
            resp = send_cloudwatch_metrics(kpis)
            logging.debug('Sent metrics to CloudWatch response:{}'.format(resp))

    except Exception as e:
       logging.error(e)
       raise e
    return {
        "StatusCode": 200,
        "ProductId" : product_id,
        "DatasetId": dataset_id,
        "RevisionId": revision_id,
        "JobId": job_id,
        # "RevisionMapIndex": revision_index,
        # "JobMapIndex": job_index,
        "JobStatus": job_status
    }


def send_metrics_rest_api(data):
    """Send metrics to a metric endpoint"""
    logging.info('Sending metric data:{}'.format(data))
    metricURL = "https://metrics.awssolutionsbuilder.com/generic"
    http = urllib3.PoolManager()
    encoded_data = json.dumps(data).encode('utf-8')
    response = None
    try:
        response = http.request('POST',metricURL,body=encoded_data,headers={'Content-Type': 'application/json'})
    except Exception as e:
        logging.error(e)
        # raise e

    return response


def send_cloudwatch_metrics(data):
    """Send custome metrics to CloudWatch"""
    cloudwatch = boto3.client('cloudwatch')
    logging.info('Sending CloudWatch custom metric:{}'.format(data))
    response = None
    try:
        response = cloudwatch.put_metric_data(
            MetricData = [
                {
                    'MetricName': 'KPIs',
                    'Dimensions': [{'Name': k, 'Value': data[k]} for k in data],
                    'Unit': 'None',
                    'Value': random.randint(1, 500)
                },
            ],
            Namespace='ADX_Publishing_Workflow/{}'.format('test') # company_name
        )
    except Exception as e:
       logging.error(e)
    #    raise e

    return response


