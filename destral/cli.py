import os
import sys
import subprocess
import unittest

from destral.utils import detect_module
from destral.openerp import OpenERPService


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
        suite = unittest.TestLoader().loadTestsFromName('addons.%s' % module)
        if not suite.countTestCases():
            suite = unittest.TestLoader().loadTestsFromName('destral.testing')
        unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()