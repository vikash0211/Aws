import os
import threading
import time
import utils
from lib.aws_connection import Aws
from lib.aws_lib import AWS_Lib
from utils import Global
from utils import common_topology, aws_topology

logger = utils.get_logger()

class Accounts:
    reserved = []
    reserve_dict = {}

class Aws_Common:

    def __init__(self, regions = None):

        self.common_config = utils.get_object_config(common_topology)
        self.config = utils.get_object_config(aws_topology)
        self.gov_cloud = self.config.get('gov_cloud')
        self.available_regions = self.config['regions']
        self.account_list = [k for k in self.config['aws_accounts']]

        if self.common_config['proxy'].get('http_proxy'):
            os.environ['http_proxy'] = self.common_config['proxy']['http_proxy']
        if self.common_config['proxy'].get('https_proxy'):
            os.environ['https_proxy'] = self.common_config['proxy']['https_proxy']

        if regions:
            if type(regions) == str:
                regions = [regions]
            if type(regions) != list:
                raise Exception('Expected regions type: list or str, Provided: {}'.format(type(regions)))
            self.available_regions = regions

        self.config['aws_accounts'] = {}
        for data in self.account_list:
            self.config['aws_accounts'][data['account']] = {'key': data['key'], 'key_id': data['key_id'], 'trusted': data.get('trusted')}

        self.aws = {}
        for acc, acc_data in self.config['aws_accounts'].items():
            self.aws[acc] = Aws(acc, acc_data['key_id'], acc_data['key'])

    def get_accounts(self):

        return self.account_list

    def get_regions(self):

        return self.available_regions

    def reserve_accounts(self, count):

        if type(count) != int:
            raise Exception('Count should be an Int Value')

        unreserved = [k for k in self.config['aws_accounts'].keys() if k not in Accounts.reserved]
        if len(unreserved) < count:
            logger.error('Not Enough Accounts. Available Accounts: {}, Reserve Request for: {}'.format(len(unreserved), count), To_Screen = True)
            return False

        reserved = unreserved[:count]
        Accounts.reserved.extend(reserved)
        return reserved

    def reserve_accounts_tenants(self, tenants):

        if type(tenants) == str:
            tenants = [tenants]

        if type(tenants) != list:
            raise Exception('Only list or String allowed')

        reserved = []
        for tn in tenants:
            if not Accounts.reserve_dict.get(tn):
                Accounts.reserve_dict[tn] = self.reserve_accounts(1)[0]

            reserved.append(Accounts.reserve_dict[tn])

        return reserved

    def aws_cleanup(self, regions = None):

        logger.warning('-------------------------------------------------------------', To_Screen = True)
        logger.warning('WARNING: Specified AWS Resources will be DELETED Permanantly', To_Screen = True)
        logger.warning('Press ctrl+c Now if dont want to continue', To_Screen = True)
        logger.warning('-------------------------------------------------------------', To_Screen = True)
        for i in range(11):
            logger.info('Continuing with AWS Clean-Up in: {} sec'.format(10 - i), To_Screen = True)
            time.sleep(1)

        self.result = True
        cleanup_dict = {k: False for k in self.config['aws_accounts'].keys()}
        if not regions:
            regions = self.available_regions
        if type(regions) == str:
            regions = [regions]
        if regions[0] == 'all':
            regions = Global.aws_gov_regions if self.gov_cloud else Global.aws_regions
        if not set(regions).issubset(set(Global.aws_regions + Global.aws_gov_regions)):
            raise Exception('Invalid regions specified: {}'.format([k for k in regions if k not in Global.aws_regions]))

        def __cleanup(account):

            result = True
            aws = AWS_Lib(self.aws[account], self.gov_cloud)

            if not aws.cleanup(regions, resources = self.config['resources']):
                logger.error('AWS Cleanup Failed for Account: {}'.format(account), To_Screen = True)
            else:
                logger.info('AWS Cleanup is Successfull for Account: {}'.format(account), To_Screen = True)

            if not aws.verify_cleanup(regions, resources = self.config['resources']):
                logger.error('AWS Cleanup Verification Failed for Account: {}'.format(account), To_Screen = True)
                result = False
            else:
                logger.info('AWS cleanup verified successfully for Account: {}'.format(account), To_Screen = True)

            cleanup_dict[account] = result

        # Start
        for i in range(1,6):
            thread_list = []
            accounts = [k for k, v in cleanup_dict.items() if not v]
            if not accounts:
                break

            logger.info('Cleanup Trial: {}'.format(i), To_Screen = True)
            for account in accounts:
                th = threading.Thread(target = __cleanup, args = (account, ))
                th.start()
                thread_list.append(th)
                time.sleep(2)

            while thread_list:
                thread_list[-1].join()
                thread_list.pop()

        accounts = [k for k, v in cleanup_dict.items() if not v]
        if accounts:
            logger.error('AWS Cleanup Failed for Accounts: {}'.format(accounts), To_Screen = True)
            return False

        logger.info('AWS Cleanup is Successfull', To_Screen = True)
        return True

    def aws_cleanup_verify(self, regions = None):

        result = True
        if not regions:
            regions = self.available_regions
        if type(regions) == str:
            regions = [regions]
        if regions[0] == 'all':
            regions = Global.aws_gov_regions if self.gov_cloud else Global.aws_regions
        if not set(regions).issubset(set(Global.aws_regions+ Global.aws_gov_regions)):
            raise Exception('Invalid regions specified: {}'.format([k for k in regions if k not in Global.aws_regions]))

        for account in self.config['aws_accounts'].keys():
            aws = AWS_Lib(self.aws[account])
            if not aws.verify_cleanup(regions):
                logger.error('Verification of AWS cleanup failed for Account: {}'.format(account), To_Screen = True)
                result = False
            else:
                logger.info('AWS cleanup verified successfully for Account: {}'.format(account), To_Screen = True)

        return result
