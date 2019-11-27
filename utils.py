import os
import yaml
import sys

class Global:

    logger = None
    test_path = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(test_path, 'aws_config.yml')
    aws_regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-south-1', 'ap-northeast-1',
                    'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2', 'ca-central-1',
                    'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1',
                    'sa-east-1']
    aws_gov_regions = ['us-gov-west-1', 'us-gov-east-1']

class aws_topology:
    pass

class common_topology:
    pass

def set_logger(logger):

    Global.logger = logger

def get_logger():

    if Global.logger:
        return Global.logger

    return no_logger()

class no_logger:

    def __init__(self):
        pass

    def info(self, msg, **kwrgs):
        print('INFO: {}'.format(msg))

    def error(self, msg, **kwrgs):
        print('ERROR: {}'.format(msg))

    def warning(self, msg, **kwrgs):
        print('WARNING: {}'.format(msg))

    def debug(self, msg, **kwrgs):
        print('DEBUG: {}'.format(msg))

def set_config_object(obj, config_file, tag = None, mandatory = False):

    data = None
    with open(config_file, 'r') as fh:
        data = yaml.safe_load(fh)

    if tag:
        if mandatory and not data.get(tag):
            raise Exception('{} not found in Config File: {}'.format(tag, config_file))
        data = data.get(tag, {})

    for k,v in data.items():
        setattr(obj, k, v)

def get_object_config(obj):

    data = {}
    for entry in dir(obj):
        if entry in ['__doc__', '__module__']:
            continue
        data[entry] = getattr(obj, entry)

    return data
