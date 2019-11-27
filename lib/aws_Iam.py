import os
import boto3
import re
import time
import utils
from botocore.config import Config

logger = utils.get_logger()

class IAM:

    def __init__(self, aws, region = None):

        self.aws = aws
        config = Config(retries = dict(max_attempts = 20))
        if region is None:
            self.client = boto3.client('iam', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, config = config, verify = False)
        else:
            self.client = boto3.client('iam', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, config = config, verify = False, region_name = region)

    def get_roles(self):

        return [k['RoleName'] for k in self.client.list_roles()['Roles']]

    def get_attached_policies(self, role):

        return self.client.list_attached_role_policies(RoleName = role)['AttachedPolicies']

    def delete_roles(self, roles):

        result = True
        for role in roles:
            try:
                for policy in self.get_attached_policies(role):
                    self.client.detach_role_policy(RoleName = role, PolicyArn = policy['PolicyArn'])
                    self.client.delete_policy(PolicyArn = policy['PolicyArn'])
                self.client.delete_role(RoleName = role)
            except Exception as e:
                logger.error('Exception while deleting Role: {}, Exception: {}'.format(role, e), To_Screen = True)
                result = False
            else:
                logger.info('Deleted Role: {}'.format(role), To_Screen = True)

        return result

    def resource_cleanup(self, resources):

        all_names = self.get_roles()
        name_list = all_names if resources else []
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

        return self.delete_roles(name_list)
