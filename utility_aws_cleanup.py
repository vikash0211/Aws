import os
import argparse
import utils
from scripts.aws_common import Aws_Common
from utils import Global
from utils import common_topology, aws_topology

logger = utils.get_logger()
parser = argparse.ArgumentParser(description = "Hcloud Cleanup")
parser.add_argument('--config_file', help = "Config File")
parser.add_argument('-R', '--all_regions', action='store_true', help = "All Regions to be cleaned up")

args, unknown = parser.parse_known_args()

def aws_cleanup():

    cloud = Aws_Common()
    regions = 'all' if args.all_regions else None
    if not cloud.aws_cleanup(regions):
        logger.error('AWS Cleanup Failed for one or more accounts', To_Screen = True)
        return False

    return True


Global.config_file = args.config_file if args.config_file else Global.config_file
utils.set_config_object(common_topology, Global.config_file, 'COMMON', True)
utils.set_config_object(aws_topology, Global.config_file, 'AWS')
aws_cleanup()
