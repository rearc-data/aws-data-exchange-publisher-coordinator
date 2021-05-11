import json
import boto3
import os
import logging
from datetime import datetime
import urllib3
import random


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
        
        logging.debug('event={}'.format(event))

        s3 = boto3.client(service_name='s3') 

        bucket = event['Bucket'] 
        key = event['Key']
        product_id = s3_select(bucket, key, """SELECT * FROM s3object[*].product_id r;""") #event['ProductId']
        dataset_id = s3_select(bucket, key, """SELECT * FROM s3object[*].dataset_id r;""") #event['DatasetId']

        logging.debug("bucket: {}\nkey: {}\nproduct_id: {}\ndatset_id: {}".format(bucket, key, product_id, dataset_id ))

        select_expression = """SELECT COUNT(*) FROM s3object[*].asset_list_10k[*] r;"""
        num_revisions = s3_select(bucket, key, select_expression)

        num_assets = 0
        num_revision_assets = 0
        if num_revisions:
            logging.info("Creating the input list to create {} revisions".format(num_revisions))
            revision_map_input_list = list(range(num_revisions))

            
            for revisions_index in range(num_revisions):
                select_expression = """SELECT COUNT(*) FROM s3object[*].asset_list_10k[{}][*] r;""".format(revisions_index)
                num_revision_assets = s3_select(bucket, key, select_expression)
                num_assets += num_revision_assets

        send_metrics = os.getenv('AnonymousUsage')
        if send_metrics == "Yes":
            kpis = {
                "Version" : os.getenv('Version'),
                "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
                "ProductId" : product_id,
                "DatasetId": dataset_id,
                "RevisionAssetCount" : num_revision_assets,
                "TotalAssetCount": num_assets,
                "RevisionMapInput": revision_map_input_list
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
        "Message": "Input generated for {} revisions and {} assets".format(num_revisions, num_assets),
        "Bucket": bucket,
        "Key": key,
        "ProductId" : product_id,
        "DatasetId": dataset_id,
        "RevisionCount": num_revisions,
        "AssetCount": num_assets,
        "RevisionMapInput": revision_map_input_list
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


