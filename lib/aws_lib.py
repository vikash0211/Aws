import os
import time
import copy
import json
import threading
import utils
from utils import Global

logger = utils.get_logger()

class AWS_Lib:

    def __init__(self, aws, gov_cloud = None):
        self.aws = aws
        self.gov_cloud = gov_cloud

    def delete_ec2_instances(self, region):

        ec2 = self.aws.get_EC2(region)
        return ec2.terminate_Instances()

    def verify_terminated_Instances(self, region):

        ec2 = self.aws.get_EC2(region)
        return ec2.verify_terminated_Instances()

    def upload_file_s3(self, file_path):

        postfix = time.strftime('%m%d-%H%M%S%M')
        file_name, file_ext = '.'.join(os.path.split(file_path)[-1].split('.')[:-1]), os.path.split(file_path)[-1].split('.')[-1]
        bucket_name = '{}-{}'.format(file_name, postfix)
        remote_file_name = '{}.{}'.format(file_name, file_ext)

        s3 = self.aws.get_S3()
        try:
            url = s3.upload_file(file_path, bucket_name, remote_file_name)
        except Exception as e:
            logger.error('Issue in uploading Capic AMI Template: {}'.format(e), To_Screen = True)
            return False

        logger.info('Uploaded File S3 url: {}'.format(url), To_Screen = True)

        return True

    def get_vpc(self, region, cidr_list):

        ec2 = self.aws.get_EC2(region)
        vpcs = ec2.get_VpcList()
        if not vpcs:
            logger.error('Vpc list not retreived from AWS', To_Screen = True)
            return False

        for vpcid in vpcs:
            vpc = ec2.get_Vpc(vpcid)
            if set(vpc.cidr) == set(cidr_list):
                return vpcid

        logger.error('Vpc not found for cidr: {}'.format(cidr_list), To_Screen = True)
        return False

    def get_instances(self, region, vpc = None):

        filters = None
        if vpc:
            filters = [{'Name': 'vpc-id', 'Values': [vpc]}]
        ec2 = self.aws.get_EC2(region)
        return ec2.get_RunningInstanceList(filters = filters)

    def get_subnet(self, region, cidr):

        ec2 = self.aws.get_EC2(region)

        subnet_list = ec2.get_SubnetList()
        for subnet_id in subnet_list:
            subnet = ec2.get_Subnet(subnet_id)
            if subnet.cidr == cidr:
                logger.info('Subnet Id: {}'.format(subnet_id), To_Screen = True)
                return subnet_id

        logger.error('Subnet not found for cidr: {}'.format(cidr), To_Screen = True)
        return False

    def get_instance_sg(self, region, instance_id):

        ec2 = self.aws.get_EC2(region)
        instance = ec2.get_Instance(id = instance_id)
        return instance.security_groups

    def create_EC2Instances(self, region, subnet_id, selector_type, selector_val, image_id = None, instance_type = None, count = 1):

        ec2 = self.aws.get_EC2(region)
        instance = ec2.get_Instance()
        key_pair = ec2.get_KeyPair()
        template = ec2.get_LaunchTemplate()
        if not instance_type:
            instance_type = 't2.micro'

        default_image = {'us-east-1': 'ami-6871a115',
                            'us-east-2':'ami-03291866',
                            'us-west-1': 'ami-18726478',
                            'us-west-2': 'ami-28e07e50',
                            'ap-south-1': 'ami-5b673c34',
                            'ap-northeast-1': 'ami-6b0d5f0d',
                            'ap-northeast-2': 'ami-3eee4150',
                            'ap-southeast-1': 'ami-76144b0a',
                            'ap-southeast-2': 'ami-67589505',
                            'ca-central-1': 'ami-49f0762d',
                            'eu-central-1': 'ami-c86c3f23',
                            'eu-west-1': 'ami-7c491f05',
                            'eu-west-2': 'ami-7c1bfd1b',
                            'eu-west-3': 'ami-5026902d',
                            'eu-north-1': '',
                            'sa-east-1': 'ami-b0b7e3dc'}
        if not image_id:
            image_id = default_image[region]

        ip_list = []
        if selector_type.lower() == 'ip':
            subnet = ec2.get_Subnet(subnet_id)
            ip_list = subnet.get_ips(selector_val)
            if not ip_list:
                logger.info('Skipping Instance Creation if selector is not part of Subnet', To_Screen = True)
                return True
        elif selector_type.lower() == 'tag_value':
            subnet = ec2.get_Subnet(subnet_id)
            ip_list = subnet.get_ips()[::-1]

        keypair_name = 'key_{}'.format(region)
        if not key_pair.create(name = keypair_name):
            logger.error('Failed to create the Key Pair', To_Screen = True)
            return False

        data = {
                    'SubnetId': subnet_id,
                    'ImageId': image_id,
                    'InstanceType': instance_type,
                    'KeyName': keypair_name, 
                    'SelectorType': selector_type,
                    'SelectorVal': selector_val
                }
        instance_list = instance.create(data = data, count = count, ips = ip_list)
        if instance_list == 0:
            pass
        if not instance_list:
            logger.error('Account: {}, Region: {}, Subnet: {}, Failed to create the EC2 Instances'.format(self.aws.account, region, subnet_id), To_Screen = True)
            return False

        for instance_id in instance_list:
            instance = ec2.get_Instance(id = instance_id, all_data = False)
            instance.wait_until_exists()

        logger.info('{} | {} | {} | {} | {} | EC2 Instance: {}'.format(self.aws.account, region, subnet_id, count, (selector_type, selector_val), instance_list), To_Screen = True)
        return True

    def create_EC2Instances_Template(self, region, subnet_id, selector_type, selector_val, image_id = None, instance_type = None, count = 1):

        ec2 = self.aws.get_EC2(region)
        instance = ec2.get_Instance()
        key_pair = ec2.get_KeyPair()
        template = ec2.get_LaunchTemplate()
        if not instance_type:
            instance_type = 't2.micro'

        default_image = {'us-east-1': 'ami-6871a115',
                            'us-east-2':'ami-03291866',
                            'us-west-1': 'ami-18726478',
                            'us-west-2': 'ami-28e07e50',
                            'ap-south-1': 'ami-5b673c34',
                            'ap-northeast-1': 'ami-6b0d5f0d',
                            'ap-northeast-2': 'ami-3eee4150',
                            'ap-southeast-1': 'ami-76144b0a',
                            'ap-southeast-2': 'ami-67589505',
                            'ca-central-1': 'ami-49f0762d',
                            'eu-central-1': 'ami-c86c3f23',
                            'eu-west-1': 'ami-7c491f05',
                            'eu-west-2': 'ami-7c1bfd1b',
                            'eu-west-3': 'ami-5026902d',
                            'eu-north-1': '',
                            'sa-east-1': 'ami-b0b7e3dc'}
        if not image_id:
            image_id = default_image[region]

        ip_list = []
        if selector_type.lower() == 'ip':
            subnet = ec2.get_Subnet(subnet_id)
            ip_list = subnet.get_ips(selector_val)
            if not ip_list:
                logger.info('Skipping Instance Creation if selector is not part of Subnet', To_Screen = True)
                return True
        elif selector_type.lower() == 'tag_value':
            subnet = ec2.get_Subnet(subnet_id)
            ip_list = subnet.get_ips()[::-1]

        keypair_name = 'key_{}'.format(subnet_id)
        if not key_pair.create(name = keypair_name):
            logger.error('Failed to create the Key Pair', To_Screen = True)
            return False

        template_name = None
        if type(selector_val) == list:
            template_name = 'template_{}_{}'.format(subnet_id, selector_val[0])
        else:
            template_name = 'template_{}_{}'.format(subnet_id, selector_val)

        template_id = template.create(name = template_name, subnet_id = subnet_id,
                            image_id = image_id, instance_type = instance_type,
                            key_pair = keypair_name, selector_type = selector_type, selector_val = selector_val)
        if template_id == 0:
            logger.info('Skipping Instance Creation if zone or region not matching.', To_Screen = True)
            return True
        if not template_id:
            logger.error('Failed to create the Launch Template', To_Screen = True)
            return False

        instance_list = instance.create(template_id = template_id, count = count, ips = ip_list)
        if not instance_list:
            logger.error('Account: {}, Region: {}, Subnet: {}, Failed to create the EC2 Instances'.format(self.aws.account, region, subnet_id), To_Screen = True)
            return False

        for instance_id in instance_list:
            instance = ec2.get_Instance(id = instance_id, all_data = False)
            instance.wait_until_exists()

        logger.info('{} | {} | {} | {} | {} | EC2 Instance: {}'.format(self.aws.account, region, subnet_id, count, (selector_type, selector_val), instance_list), To_Screen = True)
        return True

    def get_EC2Resources(self, region):

        ''' Fetch current resources from AWS '''

        ec2 = self.aws.get_EC2(region)
        ec2_filter = [{'Name': 'tag-key', 'Values': ['AciDnTag']}]
        ec2_data = {}
        ec2_resource_types = ec2.get_ResourceTypes()
        for resource_type in ec2_resource_types:
            ec2_data[resource_type] = ec2.get_Resource_List(resource_type, ec2_filter)

        return ec2_data

    def cleanup(self, regions, resources):

        self.result = True
        if type(regions) == str:
            regions = [regions]
        if type(regions) != list:
            raise Exception('Only string or list allowed for regions, Provided: {}'.format(type(regions)))

        def __cleanup(region):

            if self.gov_cloud:
                s3 = self.aws.get_S3(region = region)
                if not s3.resource_cleanup(resources.get('s3_bucket', {})):
                    self.result = False

                #IAM Role
                iam = self.aws.get_IAM(region = region)
                if not iam.resource_cleanup(resources.get('iam', {})):
                    self.result = False

            # Resource Group
            if not self.gov_cloud:
               rg = self.aws.get_ResourceGroup(region)
               if not rg.resource_cleanup(resources.get('resource_group', {})):
                   self.result = False

            # LoadBalancer
            lb = self.aws.get_LoadBalancer(region)
            if not lb.resource_cleanup(resources.get('load_balancer', {})):
                self.result = False

            # EC2
            ec2 = self.aws.get_EC2(region)
            try:
                ec2.resource_cleanup(resources.get('ec2', {}))
            except Exception as e:
                logger.error('Exception while Cleaning up region {}: {}'.format(region, e), To_Screen = True)
                self.result = False

            # Cloud Formation
            cf = self.aws.get_CloudFormation(region)
            if not cf.resource_cleanup(resources.get('stack', {})):
                self.result = False

            return self.result

        # START
        if not self.gov_cloud:
            # S3
            s3 = self.aws.get_S3()
            if not s3.resource_cleanup(resources.get('s3_bucket', {})):
                self.result = False

            #IAM Role
            iam = self.aws.get_IAM()
            if not iam.resource_cleanup(resources.get('iam', {})):
                self.result = False

        thread_list = []
        for region in regions:
            th = threading.Thread(target = __cleanup, args = (region, ))
            th.start()
            thread_list.append(th)
            time.sleep(2)

        while thread_list:
            thread_list[-1].join()
            thread_list.pop()

        return self.result

    def verify_cleanup(self, regions, resources):

        ''' Verify if AWS is cleaned up '''

        result = True
        if type(regions) == str:
            regions = [regions]
        if type(regions) != list:
            raise Exception('Only string or list allowed for regions, Provided: {}'.format(type(regions)))
        logger.info('ACCOUNT: {}'.format(self.aws.account), To_Screen = True)

        # EC2
        for region in regions:
            ec2_data = self.get_EC2Resources(region)
            ec2 = self.aws.get_EC2(region)
            logger.info('  REGION: {}'.format(region), To_Screen = True)
            for resource_type, resource_list in ec2_data.items():
                if not resource_list:
                    logger.info('    {:40}: {:<20}'.format(resource_type, 'Cleaned UP'), To_Screen = True)
                    continue

                logger.info('    {}: '.format(resource_type), To_Screen = True)
                cleaned = True
                for resource_id in resource_list:
                    state = ec2.is_Resource_Alive(resource_type, resource_id)
                    if not state[0]:
                        logger.info('      {}: {}'.format(resource_id, state[1]), To_Screen = True)
                    else:
                        logger.error('      {}: {}'.format(resource_id, state[1]), To_Screen = True)
                        cleaned = False

                if cleaned:
                    logger.info('    {:40}: {:<20}'.format(resource_type, 'Cleaned UP'), To_Screen = True)
                else:
                    logger.info('    {:40}: {:<20}'.format(resource_type, 'Not Cleaned UP'), To_Screen = True)
                    result = False

            if self.gov_cloud:
                s3 = self.aws.get_S3(region = region)
                s3_data = {}
                s3_data['Bucket_List'] = s3.get_bucket_list(filters = 'capic')

        # S3
        if not self.gov_cloud:
            s3 = self.aws.get_S3()
            s3_data = {}
            s3_data['Bucket_List'] = s3.get_bucket_list(filters = 'capic')

        for resource_type, resource_list in s3_data.items():
            if not resource_list:
                logger.info('  {:40}: {:<20}'.format(resource_type, 'Cleaned UP'), To_Screen = True)
                continue

            print('  {}: '.format(resource_type))
            for resource_id in resource_list:
                logger.error('    {}'.format(resource_id), To_Screen = True)
                cleaned = False

            if cleaned:
                logger.info('  {:40}: {:<20}'.format(resource_type, 'Cleaned UP'), To_Screen = True)
            else:
                logger.info('  {:40}: {:<20}'.format(resource_type, 'Not Cleaned UP'), To_Screen = True)
                #result = False

        return result
