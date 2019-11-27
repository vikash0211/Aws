import os
import boto3
import re
import time
import utils
from botocore.config import Config

logger = utils.get_logger()

class CloudFormation:

    def __init__(self, aws, region):

        self.aws = aws
        config = Config(retries = dict(max_attempts = 20))
        self.resource = boto3.resource('cloudformation', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, region_name = region, config = config)
        self.client = boto3.client('cloudformation', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, region_name = region, config = config)

    def get_StackOutput(self, stack_name):

        stack_output = None
        for stack in self.client.describe_stacks()['Stacks']:
            if stack_name not in stack['StackId']:
                continue

            stack_output = {k['OutputKey']: k['OutputValue'] for k in stack['Outputs']}
            break
        else:
            logger.error('Failed to get Stack output as Stack {} not found'.format(stack_name), To_Screen = True)
            raise stackIpNotFound("Failed to find stack: {}".format(stack_name))

        return stack_output

    def get_StackGlobalIp(self, stack_name):

        stack_global_ip = None
        for stack in self.client.describe_stacks()['Stacks']:
            if stack_name in stack['StackId']:
                stack_global_ip = stack['Outputs'][0]['OutputValue']
                break
        else:
            msg = "Failed to provide Elastic IP for stack: {}".format(stack_name)
            logger.error(msg, To_Screen = True)
            raise stackIpNotFound("Failed to provide Elastic IP for stack: {}".format(stack_name))

        return stack_global_ip

    def get_StackList(self, stack_filter = None):

        if not stack_filter:
            stack_list = [k['StackName'] for k in self.client.list_stacks()['StackSummaries']]
            return list(set(stack_list))

        status_list = ['CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE',
                        'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'DELETE_COMPLETE', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                        'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                        'UPDATE_ROLLBACK_COMPLETE', 'REVIEW_IN_PROGRESS']

        if type(stack_filter) == str:
            stack_filter = [stack_filter]
        if type(stack_filter) != list:
            raise Exception('List or String is expected for stack_filter, Provided: {}'.format(type(stack_filter)))
        if any([k not in status_list for k in stack_filter]):
            raise Exception('Invalid stack_filter: {}'.format([k for k in stack_filter if k not in status_list]))

        stack_list = [k['StackName'] for k in self.client.list_stacks(StackStatusFilter = stack_filter)['StackSummaries']]
        return list(set(stack_list))

    def resource_cleanup(self, resources):

        all_names = self.get_StackList()
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

        return self.delete_stack(name_list)

    def delete_stack(self, stacks, max_wait = None):

        if type(stacks) == str:
            stacks = [stacks]
        max_wait = max_wait if max_wait else 900
        retry_gap = 30

        def __delete(stack_name):

            if stack_name not in self.get_StackList():
                logger.info('No Stack found with Name: {}'.format(stack_name), To_Screen = True)
                return True

            response = self.client.delete_stack(StackName = stack_name)
            for i in range(1, int(max_wait/retry_gap) + 1):
                for stack in self.client.list_stacks()['StackSummaries']:
                    if stack['StackName'] != stack_name:
                        continue
                    if stack['StackStatus'] != 'DELETE_COMPLETE' :
                        logger.info('{}. Stack: {}, Status: {}'.format(i, stack_name, stack['StackStatus']), To_Screen = True)
                        break
                else:
                    logger.info('{}. Stack: {}, Status: DELETE_COMPLETE'.format(i, stack_name), To_Screen = True)
                    break
                time.sleep(retry_gap)
            else:
                logger.error('Stack: {} deletion is stuck for last {} sec, Check problem on AWS'.format(stack_name, max_wait), To_Screen = True)
                return False

            logger.info('Deleted Stack: {}'.format(stack_name), To_Screen = True)
            return True

        result = True
        for stack in stacks:
            result &= __delete(stack)

        return result

    def create_stack(self, template, max_wait = None):

        stack_name = template['StackName']

        # Delete stack if already exist
        if not self.delete_stack(stack_name):
            raise StackDeleteFailed('Stack Deletion hang')

        logger.info('Creating stack with name: {}'.format(stack_name), To_Screen = True)

        # Create Stack
        capabilities = template.get('Capabilities')
        try:
            if not capabilities:
                response  = self.client.create_stack(StackName = stack_name, TemplateURL = template['TemplateURL'],
                                                Parameters = template['Parameters'])
            else:
                response  = self.client.create_stack(StackName = stack_name, TemplateURL = template['TemplateURL'],
                                                Parameters = template['Parameters'], Capabilities = capabilities)
        except Exception as e:
            logger.error('Failed to Create Stack: {}, Exception: {}'.format(stack_name, e), To_Screen = True)
            raise stackCreationFailed(e)

        if stack_name not in self.get_StackList(stack_filter = []):
            logger.error('Stack {} not found in stack list, Issue in creation'.format(stack_name), To_Screen = True)
            raise stackCreationFailed("Stack Not Created: {}".format(stack_name))

        max_wait = max_wait if max_wait else 600
        retry_gap = 30
        for i in range(1, int(max_wait/retry_gap) + 1):
            stack_status = None
            for stack in self.client.list_stacks()['StackSummaries']:
                if stack['StackName'] != stack_name:
                    continue

                stack_status = stack['StackStatus']
                break
            else:
                raise stackCreationFailed("Stack Status not found for: {}".format(stack_name))

            logger.info('{}. Stack Status: {}'.format(i, stack_status), To_Screen = True)
            if stack_status == 'CREATE_COMPLETE':
                break
            if stack_status in ['ROLLBACK_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'CREATE_FAILED']:
                logger.info('Check AMI exist or other reason for Rollback', To_Screen = True)
                raise stackCreationFailed("Stack RolledBack: {}".format(stack_name))
            time.sleep(retry_gap)
        else:
            logger.error('Stack Creation is stuck for last {} sec, Check problem on AWS'.format(max_wait), To_Screen = True)
            raise stackCreationFailed('Stack Creation hang')

        return stack_name

