import os
import boto3
import re
import time
import utils
from botocore.config import Config

logger = utils.get_logger()

class ResourceGroup:

    def __init__(self, aws, region):

        self.aws = aws
        self.region = region
        config = Config(retries = dict(max_attempts = 20))
        self.client = boto3.client('resource-groups', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, region_name = region, config = config, verify = False)

    def list_groups(self):

        group_names = []
        groups = self.client.list_groups()
        group_names = [k.get('Name') for k in groups['Groups']]
        logger.info('Groups: {}'.format(group_names), To_Screen = True)

        return group_names

    def delete_groups(self, groups):

        result = True
        for name in groups:
            try:
                self.client.delete_group(GroupName = name)
            except Exception as e:
                logger.error('Exception while deleting Resource Group: {}, Exception: {}'.format(name, e), To_Screen = True)
                result = False
            else:
                logger.info('Deleted Resource Group: {}'.format(name), To_Screen = True)

        return result

    def resource_cleanup(self, resources):

        all_names = self.list_groups()
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

        return self.delete_groups(name_list)
