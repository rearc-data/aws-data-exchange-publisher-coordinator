import json
import boto3
import os
import logging
from botocore.config import Config
from datetime import datetime
import random
import time


def lambda_handler(event, context):
    """This job finalizes the current revision and adds it to ADX product"""
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
        revision_index = event['RevisionMapIndex']
        
        dataexchange = boto3.client(service_name='dataexchange')

        finalize_response = dataexchange.update_revision(RevisionId=revision_id, DataSetId=dataset_id, Finalized=True)
        marketplace_config = Config(region_name='us-east-1')
        marketplace = boto3.client(service_name='marketplace-catalog', config=marketplace_config)
        logging.debug('finalize={}'.format(finalize_response))
    
        product_details = marketplace.describe_entity(EntityId=product_id, Catalog='AWSMarketplace')
        logging.debug('describe_entity={}'.format(product_details))

        entity_id = product_details['EntityIdentifier'] 
        revision_arns = finalize_response['Arn']
        arn_parts = finalize_response['Arn'].split("/")
        dataset_arn = arn_parts[0] + '/' + arn_parts[1]

        logging.debug('EntityIdentifier={}'.format(entity_id))
        logging.debug('DataSetArn={}'.format(dataset_arn))
        product_update_change_set = [{
            'ChangeType' : 'AddRevisions',
            'Entity' : {
                'Identifier' : entity_id,
                'Type' : 'DataProduct@1.0'
            },
            'Details' : '{"DataSetArn":"' + dataset_arn + '","RevisionArns":["' + revision_arns + '"]}'
        }]
        logging.info('product update change set = {}'.format(json.dumps(product_update_change_set)))

        changeset_response = marketplace.start_change_set(Catalog='AWSMarketplace', 
                                                            ChangeSet=product_update_change_set)
        logging.debug('changeset={}'.format(changeset_response))

        done = False
        while not done:
            time.sleep(1)
            change_set_id = changeset_response['ChangeSetId']
            
            describe_change_set = marketplace.describe_change_set(
                    Catalog='AWSMarketplace', ChangeSetId=change_set_id)
            
            describe_change_set_status = describe_change_set['Status']
            
            if describe_change_set_status == 'SUCCEEDED':
                logging.info('Change set succeeded')
                done = True
            
            if describe_change_set_status == 'FAILED':
                raise Exception("#{}\n#{}".format(describe_change_set["failure_description"], describe_change_set["change_set"]["first"]["error_detail_list"].join()))
        
        metrics = {
            "Version" : os.getenv('Version'),
            "TimeStamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "ProductId" : product_id,
            "DatasetId": dataset_id,
            "RevisionId": revision_id,
            "RevisionMapIndex": revision_index
        }
        logging.info('Metrics:{}'.format(metrics))

    except Exception as e:
       logging.error(e)
       raise e
    return {
        "StatusCode": 200,
        "Message": "Revision Finalized and Product Updated",
        "ProductId" : product_id,
        "DatasetId": dataset_id,
        "RevisionId": revision_id,
        "RevisionMapIndex": revision_index
    }



