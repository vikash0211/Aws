import mTest
from mTest import Hide, GoTo
from pyMusk import Data
import os
import sys
import utils
from utils import Global
from utils import common_topology, aws_topology

utils.set_logger(Data.logger)
logger = utils.get_logger()

from scripts.aws_common import Aws_Common

class Common_Setup(mTest.TestCase):

    def config_setup(self, test_args):

        config_file = test_args.get('config_file')
        if test_args.get('config_file'):
            Global.config_file = test_args['config_file']

        utils.set_config_object(common_topology, Global.config_file, 'COMMON', True)
        utils.set_config_object(aws_topology, Global.config_file, 'AWS')
        return True


class Common_Cleanup(mTest.TestCase):

    def aws_cleanup(self, test_args):

        config_file = test_args.get('config_file')
        regions = test_args.get('regions')
        cloud = Aws_Common()

        return cloud.aws_cleanup(regions = regions)
