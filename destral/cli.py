import os
import sys
import subprocess
import unittest
import logging

from destral.utils import detect_module
from destral.openerp import OpenERPService


logging.basicConfig(level=logging.DEBUG)


def main():
    OpenERPService()
    if len(sys.argv) < 2:
        paths = subprocess.check_output([
            "git", "diff", "--name-only", "HEAD~1..HEAD"
        ])
        paths = [x for x in paths.split('\n') if x]
        modules_to_test = []
        for path in paths:
            module = detect_module(path)
            if module and module not in modules_to_test:
                modules_to_test.append(module)

    else:
        modules_to_test = sys.argv[1:]
    for module in modules_to_test:
        os.environ['OOTEST_MODULE'] = module
        tests_module = 'addons.{}.tests'.format(module)
        try:
            suite = unittest.TestLoader().loadTestsFromName(tests_module)
        except AttributeError:
            suite = unittest.TestSuite()
        if not suite.countTestCases():
            suite = unittest.TestLoader().loadTestsFromName('destral.testing')
        unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()