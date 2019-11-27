import os
import boto3
import re
import time
import utils
from botocore.config import Config

logger = utils.get_logger()

class LoadBalancer:

    def __init__(self, aws, region):

        self.aws = aws
        self.region = region
        config = Config(retries = dict(max_attempts = 20))
        self.client = boto3.client('elbv2', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, region_name = region, config = config, verify = False)

    def list_lbs(self):

        response = self.client.describe_load_balancers(Names = [])
        return [k.get('LoadBalancerName') for k in response['LoadBalancers']]

    def get_lb_arn(self, name):

        response = self.client.describe_load_balancers(Names = [name])
        return response['LoadBalancers'][0]['LoadBalancerArn']

    def delete_lbs(self, lb_list):

        result = True
        for name in lb_list:
            try:
                self.client.delete_load_balancer(LoadBalancerArn = self.get_lb_arn(name))
            except Exception as e:
                logger.error('Exception while deleting Load Balancer: {}, Exception: {}'.format(name, e), To_Screen = True)
                result = False
            else:
                logger.info('Deleted Load Balancer: {}'.format(name), To_Screen = True)

        return result

    def resource_cleanup(self, resources):

        all_names = self.list_lbs()
        name_list = all_names
        if not resources.get('all'):
            name_list = [k for k in all_names if k in resources.get('name', [])]
            resource_filter = resources.get('filter', {})
            for fltr in resource_filter.get('name', []):
                if not resource_filter.get('ignore_case'):
                    name_list.extend([k for k in all_names if fltr in k])
                else:
                    name_list.extend([k for k in all_names if fltr.lower() in k.lower()])
            name_list = list(set(name_list))
            name_list = [k for k in name_list if k not in resources.get('exclude_name', [])]

        return self.delete_lbs(name_list)
