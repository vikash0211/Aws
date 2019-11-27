import os
import boto3
import re
import time
import utils
from botocore.config import Config

logger = utils.get_logger()

class S3:

    def __init__(self, aws, region = None):

        self.aws = aws
        config = Config(retries = dict(max_attempts = 20))
        if region is not None:
            self.resource = boto3.resource('s3', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, config = config, region_name = region)
            self.client = boto3.client('s3', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, config = config, region_name = region)
        else:
            self.resource = boto3.resource('s3', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, config = config)
            self.client = boto3.client('s3', aws_access_key_id = aws.key_id, aws_secret_access_key = aws.key, config = config)

    def get_buckets(self):

        buckets_dict = self.client.list_buckets()
        return [k for k in buckets_dict['Buckets']]


    def get_bucket_list(self, filters = None):

        buckets = self.get_buckets()
        if not filters:
            return [k['Name'] for k in buckets]
        return [k['Name'] for k in buckets if filters in k['Name']]

    def delete_buckets(self, bucket_list):

        result = True
        for name in bucket_list:
            try:
                bucket = self.resource.Bucket(name)
                bucket.objects.all().delete()
                bucket.delete()
            except Exception as e:
                logger.error('Exception while deleting Bucket: {}, Exception: {}'.format(name, e), To_Screen = True)
                result = False
            else:
                logger.info('Deleted Bucket: {}'.format(name), To_Screen = True)

        return result

    def resource_cleanup(self, resources):

        all_names = self.get_bucket_list()
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

        return self.delete_buckets(bucket_list = name_list)


    def upload_file(self, local_file_name, bucket_name, remote_file_name):

        '''
        Create a bucket in the specified bucket with remote file name.
        '''

        # Delete bucket if already exist
        if bucket_name in self.get_bucket_list():
            self.delete_buckets([bucket_name])

        # Create Bucket
        self.client.create_bucket(Bucket = bucket_name)
        self.client.upload_file(local_file_name, bucket_name, remote_file_name)

        # Check file uploaded
        if bucket_name not in self.get_bucket_list():
            raise s3BucketNotFound('Bucket not created: {}'.format(bucket_name))

        bucket = self.resource.Bucket(bucket_name)
        objs = list(bucket.objects.filter(Prefix = remote_file_name))
        if not objs:
            raise s3FileNotFound('File not uploaded: {}'.format(remote_file_name))

        object_acl = self.resource.ObjectAcl(bucket_name, remote_file_name)
        response = object_acl.put(ACL='public-read')

        return "https://s3.amazonaws.com/{}/{}".format(bucket_name, remote_file_name)

    def upload_file_gov(self, local_file_name, bucket_name, remote_file_name, region):

        '''
        Create a bucket in the specified bucket with remote file name.
        '''

        # Delete bucket if already exist
        if bucket_name in self.get_bucket_list():
            self.delete_buckets([bucket_name])

        # Create Bucket
        self.client.create_bucket(Bucket=bucket_name,CreateBucketConfiguration={'LocationConstraint': region},)
        self.resource.meta.client.upload_file(local_file_name, bucket_name, remote_file_name)

        # Check file uploaded
        if bucket_name not in self.get_bucket_list():
            raise s3BucketNotFound('Bucket not created: {}'.format(bucket_name))

        bucket = self.resource.Bucket(bucket_name)
        objs = list(bucket.objects.filter(Prefix = remote_file_name))
        if not objs:
            raise s3FileNotFound('File not uploaded: {}'.format(remote_file_name))

        object_acl = self.resource.ObjectAcl(bucket_name, remote_file_name)
        response = object_acl.put(ACL='public-read')

        return "https://s3-{}.amazonaws.com/{}/{}".format(region,bucket_name, remote_file_name)


