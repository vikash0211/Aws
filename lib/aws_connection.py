import os
import boto3
import re
import time
import utils
from lib.aws_S3 import S3
from lib.aws_CloudFormation import CloudFormation
from lib.aws_ResourceGroup import ResourceGroup
from lib.aws_LoadBalancer import LoadBalancer
from lib.aws_EC2 import EC2
from lib.aws_Iam import IAM

logger = utils.get_logger()

class Aws:

    def __init__(self, account, key_id, key):

        self.account = account
        self.key_id = key_id
        self.key = key

    def get_S3(self, region = None):
        return S3(self, region = region)

    def get_CloudFormation(self, region):
        return CloudFormation(self, region)

    def get_ResourceGroup(self, region):
        return ResourceGroup(self, region)

    def get_LoadBalancer(self, region):
        return LoadBalancer(self, region)

    def get_EC2(self, region):
        return EC2(self, region)

    def get_IAM(self, region = None):
        return IAM(self, region = region)

