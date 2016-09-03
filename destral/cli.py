import os
import sys
import subprocess
import logging
import urllib2

import click
from destral.utils import *
from destral.testing import run_unittest_suite, get_unittest_suite
from destral.testing import run_spec_suite, get_spec_suite
from destral.openerp import OpenERPService
from destral.patch import RestorePatchedRegisterAll
from destral.cover import OOCoverage
from pylint import epylint as lint


LOG_FORMAT = '%(asctime)s:{0}'.format(logging.BASIC_FORMAT)

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

logger = logging.getLogger('destral.cli')


@click.command()
@click.option('--modules', '-m', multiple=True)
@click.option('--tests', '-t', multiple=True)
@click.option('--enable-coverage', type=click.BOOL, default=False, is_flag=True)
@click.option('--report-coverage', type=click.BOOL, default=False, is_flag=True)
@click.option('--enable-lint', type=click.BOOL, default=False, is_flag=True)
def destral(modules, tests, enable_coverage=None, report_coverage=None, enable_lint=None):
    sys.argv = sys.argv[:1]
    service = OpenERPService()
    if not modules:
        ci_pull_request = os.environ.get('CI_PULL_REQUEST')
        token = os.environ.get('GITHUB_TOKEN')
        if ci_pull_request and token:
            url = 'https://api.github.com/repos/{repo}/pulls/{pr_number}'.format(
                    repo=os.environ.get('CI_REPO'),
                    pr_number=ci_pull_request
                )
            req = urllib2.Request(
                url,
                headers={
                    'Authorization': 'token {0}'.format(token),
                    'Accept': 'application/vnd.github.patch'
            })
            f = urllib2.urlopen(req)
            paths = find_files(f.read())
            logger.info('Files from Pull Request: {0}: {1}'.format(
                ci_pull_request, ', '.join(paths)
            ))
        else:
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
    root_path = service.config['root_path']

    if not modules_to_test:
        if enable_lint:
            source_dir = root_path
        coverage_config = {
            'source': [root_path],
            'omit': ['*/addons/*/*']
        }
    else:
        if enable_lint:
            source_dir = coverage_modules_path(modules_to_test, addons_path)[0]
        coverage_config = {
            'source': coverage_modules_path(modules_to_test, addons_path),
            'omit': ['*/__terp__.py']
        }
    if enable_lint:
        (pylint_stdout, pylint_stderr) = lint.py_run('{} --enable=python3  --ignore __terp__.py'.format(source_dir), return_std=True)
    coverage = OOCoverage(**coverage_config)
    coverage.enabled = (enable_coverage or report_coverage)

    coverage.start()
    server_spec_suite = get_spec_suite(root_path)
    if server_spec_suite:
        logging.info('Spec testing for server')
        report = run_spec_suite(server_spec_suite)
        results.append(not len(report.failed_examples) > 0)
    coverage.stop()

    for module in modules_to_test:
        with RestorePatchedRegisterAll():
            install_requirements(module, addons_path)
            spec_suite = get_spec_suite(os.path.join(addons_path, module))
            if spec_suite:
                logger.info('Spec testing module %s', module)
                coverage.start()
                report = run_spec_suite(spec_suite)
                coverage.stop()
                results.append(not len(report.failed_examples) > 0)
            logger.info('Unit testing module %s', module)
            os.environ['DESTRAL_MODULE'] = module
            coverage.start()
            suite = get_unittest_suite(module, tests)
            result = run_unittest_suite(suite)
            coverage.stop()
            results.append(result.wasSuccessful())
    if report_coverage:
        coverage.report()
    if enable_coverage:
        coverage.save()
    if enable_lint:
        print(pylint_stdout.read())

    if not all(results):
        sys.exit(1)


if __name__ == '__main__':
    destral()
