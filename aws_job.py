import os
import sys
import argparse

testPath = os.path.dirname(os.path.abspath(__file__))
importPath = []
importPath.append(os.path.join(testPath, '../pyMusk/pyMusk'))
for path in importPath:
    if path not in sys.path:
        sys.path.append(path)

from pyMusk import Task
from pyMusk import Data
from mLogging import getReport


Data.job_dict['file'] = __file__

parser = argparse.ArgumentParser(description = 'Aws Job')
parser.add_argument('--config_file', help = "Config File")
parser.add_argument('--mail_from', help = 'Sender of Test Report')
parser.add_argument('--mail_to', help = 'Receipents to Receive the test Report (Seperated by ,)')
args, unknown = parser.parse_known_args()

task = Task()
if args.mail_from:
	task.set_sender(args.mail_from)
if args.mail_to:
	task.set_receipients(args.mail_to.split(','))

def test():

    test_script = os.path.join(testPath, 'aws_test.py')
    test_args = {}
    test_args['config_file'] = args.config_file
    test_args['regions'] = 'all'
    task.run(test_script, name = 'Cleanup', test_args = test_args, test_list = ('Common_Setup', 'Common_Cleanup'))
    return

if __name__ == '__main__':
    test()
    getReport()

