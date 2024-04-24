import os
import sys
import subprocess
import logging
import requests

import click
from destral.utils import *
from destral.testing import run_unittest_suite, get_unittest_suite
from destral.testing import run_spec_suite, get_spec_suite
from destral.linter import run_linter
from destral.openerp import OpenERPService
from destral.patch import RestorePatchedRegisterAll
from destral.cover import OOCoverage

LOG_FORMAT = '%(asctime)s:{0}'.format(logging.BASIC_FORMAT)

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

logger = logging.getLogger('destral.cli')


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.option('--modules', '-m', multiple=True)
@click.option('--tests', '-t', multiple=True)
@click.option('--all-tests', '-a', type=click.BOOL, default=False, is_flag=True)
@click.option('--enable-coverage', type=click.BOOL, default=False, is_flag=True)
@click.option('--report-coverage', type=click.BOOL, default=False, is_flag=True)
@click.option('--report-junitxml', type=click.STRING, nargs=1, default="")
@click.option('--database', type=click.STRING, nargs=1, default=None)
@click.option('--dropdb/--no-dropdb', default=True)
@click.option('--requirements/--no-requirements', default=True)
@click.option('--enable-lint', type=click.BOOL, default=False, is_flag=True)
@click.option('--constraints-file', type=click.STRING, nargs=1, default="")
def destral(modules, tests, all_tests=None, enable_coverage=None,
            report_coverage=None, report_junitxml=None, dropdb=None,
            requirements=None, **kwargs):
    os.environ['OPENERP_DESTRAL_MODE'] = "1"
    enable_lint = kwargs.pop('enable_lint')
    constraints_file = kwargs.pop('constraints_file')
    database = kwargs.pop('database')
    if database:
        os.environ['OPENERP_DB_NAME'] = database
    sys.argv = sys.argv[:1]
    service = OpenERPService()
    if report_junitxml:
        os.environ['DESTRAL_JUNITXML'] = report_junitxml
    else:
        report_junitxml = os.environ.get('DESTRAL_JUNITXML', False)
    if report_junitxml:
        junitxml_directory = os.path.abspath(report_junitxml)
        if not os.path.isdir(junitxml_directory):
            os.makedirs(junitxml_directory)
    if not modules:
        ci_pull_request = os.environ.get('CI_PULL_REQUEST')
        token = os.environ.get('GITHUB_TOKEN')
        repository = os.environ.get('CI_REPO')
        if ci_pull_request and token and repository:
            try:
                int(ci_pull_request)
            except:
                # If CI_PULL_REQUEST contains URL instead of PR number, get it
                ci_pull_request = ci_pull_request.split('/')[-1]
            url = 'https://api.github.com/repos/{repo}/pulls/{pr_number}'.format(
                repo=repository,
                pr_number=ci_pull_request
            )
            req = requests.get(
                url,
                headers={
                    'Authorization': 'token {0}'.format(token),
                    'Accept': 'application/vnd.github.patch'
                }
            )
            paths = find_files(req.text)
            logger.info('Files from Pull Request: {0}: {1}'.format(
                ci_pull_request, ', '.join(paths)
            ))
        else:
            paths = subprocess.check_output([
                "git", "diff", "--name-only", "HEAD~1..HEAD"
            ]).decode('utf-8')
            paths = [x for x in paths.split('\n') if x]
            logger.info('Files from last commit: {}'.format(
                ', '.join(paths)
            ))
        modules_to_test = []
        for path in paths:
            module = detect_module(path)
            if module and module not in modules_to_test:
                modules_to_test.append(module)
        if not modules_to_test:
            modules_to_test = ['base']
    else:
        modules_to_test = modules[:]

    results = []
    addons_path = service.config['addons_path']
    root_path = service.config['root_path']

    if not modules_to_test:
        coverage_config = {
            'source': [root_path],
            'omit': ['*/addons/*/*']
        }
    else:
        coverage_config = {
            'source': coverage_modules_path(modules_to_test, addons_path),
            'omit': ['*/__terp__.py']
        }

    coverage = OOCoverage(**coverage_config)
    coverage.enabled = (enable_coverage or report_coverage)

    junitxml_suites = []

    coverage.start()
    server_spec_suite = get_spec_suite(root_path)
    if server_spec_suite:
        logging.info('Spec testing for server')
        report = run_spec_suite(server_spec_suite)
        results.append(not len(report.failed_examples) > 0)
        if report_junitxml:
            junitxml_suites += report.create_report_suites()
    coverage.stop()
    
    logger.info('Modules to test: {}'.format(','.join(modules_to_test)))
    for module in modules_to_test:
        with RestorePatchedRegisterAll():
            if requirements:
                install_requirements(module, addons_path, constraints_file=constraints_file)
            spec_suite = get_spec_suite(os.path.join(addons_path, module))
            if spec_suite:
                logger.info('Spec testing module %s', module)
                coverage.start()
                report = run_spec_suite(spec_suite)
                coverage.stop()
                results.append(not len(report.failed_examples) > 0)
                if report_junitxml:
                    junitxml_suites += report.create_report_suites()
            logger.info('Unit testing module %s', module)
            os.environ['DESTRAL_MODULE'] = module
            coverage.start()
            try:
                suite = get_unittest_suite(module, tests)
            except Exception as e:
                logger.error('Suite not found: {}'.format(e))
                service.shutdown(1)
            suite.drop_database = dropdb
            suite.config['all_tests'] = all_tests
            if all_tests:
                for m in get_dependencies(module, addons_path):
                    for test in get_unittest_suite(m):
                        if test not in suite:
                            suite.addTest(test)
            result = run_unittest_suite(suite)
            coverage.stop()
            results.append(result.wasSuccessful())
            if report_junitxml:
                junitxml_suites.append(result.get_test_suite(module))
    if report_junitxml:
        from junit_xml import TestSuite
        for suite in junitxml_suites:
            with open(
                    os.path.join(report_junitxml, suite.name+'.xml'), 'w'
            ) as report_file:
                report_file.write(TestSuite.to_xml_string([suite]))
        logger.info('Saved report XML on {}/'.format(report_junitxml))
    if report_coverage:
        coverage.report()
    if enable_coverage:
        coverage.save()

    if enable_lint:
        modules_path = ['{}/{}'.format(addons_path, m) for m in modules_to_test]
        if modules_path:
            run_linter(modules_path)

    return_code = 0
    if not all(results):
        return_code = 1

    service.shutdown(return_code)
    sys.exit(return_code)


if __name__ == '__main__':
    destral()
