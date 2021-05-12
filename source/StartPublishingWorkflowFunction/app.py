import json
import boto3
import time
import calendar
import os
import logging
from datetime import datetime
import urllib3
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
        EXECUTION_NAME = 'Execution-ADX-PublishingWorkflow-SFN@{}'.format(str(calendar.timegm(time.gmtime()))) 
        INPUT = json.dumps({
            "Bucket" : bucket,
            "Key" : key
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

        send_metrics = os.getenv('AnonymousUsage')
        if send_metrics == "Yes":
            kpis = {
                "Version" : os.getenv('Version'),
                "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
                "Bucket" : bucket,
                "Key": key,
                "StateMachineARN" : STATE_MACHINE_ARN,
                "ExecutionName": EXECUTION_NAME
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