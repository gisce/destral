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
from tqdm import tqdm

LOG_FORMAT = '%(asctime)s:{0}'.format(logging.BASIC_FORMAT)

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

logger = logging.getLogger('destral.cli')


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.option('--modules', '-m', multiple=True)
@click.option('--tests', '-t', multiple=True)
@click.option(
    '--export-translations', type=click.BOOL, default=False, is_flag=True)
@click.option('--enable-coverage', type=click.BOOL, default=False, is_flag=True)
@click.option('--report-coverage', type=click.BOOL, default=False, is_flag=True)
@click.option('--report-junitxml', type=click.STRING, nargs=1, default=False)
@click.option('--dropdb/--no-dropdb', default=True)
@click.option('--requirements/--no-requirements', default=True)
def destral(modules, tests, export_translations=False, enable_coverage=None, report_coverage=None,
            report_junitxml=None, dropdb=None, requirements=None):
    sys.argv = sys.argv[:1]
    if not export_translations:
        export_translations = False
    if not os.environ.get('DESTRAL_EXPORT_TRANSLATIONS', False):
        os.environ['DESTRAL_EXPORT_TRANSLATIONS'] = str(export_translations)
    export_translations = eval(os.environ.get('DESTRAL_EXPORT_TRANSLATIONS', "False"))
    if export_translations:
        tests = ['OOBaseTests.test_translate_modules']
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
            req = urllib2.Request(
                url,
                headers={
                    'Authorization': 'token {0}'.format(token),
                    'Accept': 'application/vnd.github.patch'
                }
            )
            f = urllib2.urlopen(req)
            paths = find_files(f.read())
            logger.info('Files from Pull Request: {0}: {1}'.format(
                ci_pull_request, ', '.join(paths)
            ))
        else:
            paths = subprocess.check_output([
                "git", "diff", "--name-only", "HEAD~1..v2.86.3"
            ])
            paths = [x for x in paths.split('\n') if x]
        modules_to_test = []
        for path in paths:
            if '__terp__' in path:
                continue
            module = detect_module(path)
            if module and module not in modules_to_test:
                modules_to_test.append(module)
    else:
        modules_to_test = modules[:]
    print(modules_to_test)
    exit(-1)
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
    failed_modules = []
    for module in tqdm(modules_to_test):
        try:
            logger.info('Testing Module: {}'.format(module))
            with RestorePatchedRegisterAll():
                if requirements:
                    install_requirements(module, addons_path)
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
                suite = get_unittest_suite(module, tests)
                suite.drop_database = dropdb
                result = run_unittest_suite(suite)
                coverage.stop()
                results.append(result.wasSuccessful())
                if report_junitxml:
                    junitxml_suites.append(result.get_test_suite(module))
        except Exception as err:
            failed_modules.append((module, err))
    print('FAILED MODULES:')
    print(failed_modules)
    if report_junitxml:
        from junit_xml import TestSuite
        for suite in junitxml_suites:
            with open(
                    os.path.join(report_junitxml, suite.name+'.xml'), 'w'
            ) as report_file:
                report_file.write(TestSuite.to_xml_string([suite]))
    if report_coverage:
        coverage.report()
    if enable_coverage:
        coverage.save()

    if not all(results):
        sys.exit(1)


if __name__ == '__main__':
    destral()
