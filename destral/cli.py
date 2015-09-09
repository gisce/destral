import importlib
import os
import sys
import subprocess
import unittest
import logging

import click
from destral.utils import detect_module, module_exists, get_dependencies
from destral.openerp import OpenERPService


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('destral.cli')


@click.command()
@click.option('--modules', '-m', multiple=True)
@click.option('--tests', '-t', multiple=True)
def destral(modules, tests):
    sys.argv = sys.argv[:1]
    service = OpenERPService()
    if not modules:
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
        modules_to_test = modules[:]

    results = []
    addons_path = service.config['addons_path']
    for module in modules_to_test:
        for dep_module in get_dependencies(module, addons_path):
            req = os.path.join(
                service.config['addons_path'], dep_module, 'requirements.txt'
            )
            pip = os.path.join(sys.prefix, 'bin', 'pip')
            if os.path.exists(req) and os.path.exists(pip):
                logger.info('Requirements file %s found. Installing...', req)
                subprocess.check_call([pip, "install", "-r", req])
        logger.info('Testing module %s', module)
        os.environ['DESTRAL_MODULE'] = module
        tests_module = 'addons.{}.tests'.format(module)
        logger.debug('Test module: %s', tests_module)
        # Module exists but there is an error show the error
        if module_exists(tests_module) is None:
            importlib.import_module(tests_module)
        if tests:
            tests = ['{}.{}'.format(tests_module, t) for t in tests]
            suite = unittest.TestLoader().loadTestsFromNames(tests)
        else:
            try:
                suite = unittest.TestLoader().loadTestsFromName(tests_module)
            except AttributeError, e:
                logger.debug('Test suits not found...%s', e)
                suite = unittest.TestSuite()
        if not suite.countTestCases():
            suite = unittest.TestLoader().loadTestsFromName('destral.testing')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            results.append(False)
        else:
            results.append(True)

    if not all(results):
        sys.exit(1)


if __name__ == '__main__':
    destral()
