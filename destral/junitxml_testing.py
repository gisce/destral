import unittest
import junit_xml
import time
import logging

from mamba import formatters
from mamba import reporter
from mamba.application_factory import ApplicationFactory

# UNITTEST JUNITXML


class LoggerStream(object):

    @staticmethod
    def write(text):
        if text == '\n':
            text = ''
        logger = logging.getLogger('destral.testing.results')
        logger.info(text)

    @staticmethod
    def flush():
        pass


class JUnitXMLResult(unittest.result.TestResult):
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        super(JUnitXMLResult, self).__init__(stream, descriptions, verbosity)
        self.ran_tests = []
        self._time_tests = []
        self.startedAt = None
        self.endedAt = None

    def startTestRun(self):
        self.startedAt = time.time()

    def printErrors(self):
        self.endedAt = time.time()

    def startTest(self, test):
        self._time_tests.append({
            'start': time.time(),
            'end': False
        })
        super(JUnitXMLResult, self).startTest(test)

    def _end_test(self, test, type='Success', err_data=None, out_data=''):
        test_index = self.testsRun - 1
        # If already ended, do nothing
        if (len(self.ran_tests) == self.testsRun and
                self.ran_tests[test_index]):
            return
        start_time = self._time_tests[test_index]['start']
        endtime = self._time_tests[test_index]['end'] or time.time()
        if not self._time_tests[test_index]['end']:
            self._time_tests[test_index]['end'] = endtime
        test_name = str(test).split()[0]
        test_classname = str(test).split()[-1][1:-1]
        err_text = ''
        if err_data:
            err_text = self._exc_info_to_string(err_data, test)
        testcase = junit_xml.TestCase(
            name=test_name,
            classname=test_classname,
            elapsed_sec=(endtime - start_time),
            stdout=out_data,
            status=type
        )
        if testcase.status == 'Error':
            testcase.add_error_info(
                message='Error At {}'.format(test_name),
                output=err_text
            )
        elif testcase.status == 'Failure':
            testcase.add_failure_info(
                message='Failure At {}'.format(test_name),
                output=err_text
            )
        elif testcase.status == 'Skip':
            testcase.add_skipped_info(
                message='Skipped {}'.format(test_name),
                output=out_data
            )
        self.ran_tests.append(testcase)

    def stopTest(self, test):
        self._end_test(test, type='Stopped')
        super(JUnitXMLResult, self).stopTest(test)

    def addError(self, test, err):
        self._end_test(test, err_data=err, type='Error')
        super(JUnitXMLResult, self).addError(test, err)

    def addFailure(self, test, err):
        self._end_test(test, err_data=err, type='Failure')
        super(JUnitXMLResult, self).addFailure(test, err)

    def addSuccess(self, test):
        self._end_test(test)
        super(JUnitXMLResult, self).addSuccess(test)

    def addSkip(self, test, reason):
        self._end_test(test, type='Skip', out_data=reason)
        super(JUnitXMLResult, self).addSkip(test, reason)

    def get_test_suite(self, module_name):
        return junit_xml.TestSuite(
            name=module_name,
            test_cases=self.ran_tests
        )

# MAMBA JUNITXML


class JUnitXMLApplicationFactory(ApplicationFactory):
    def __init__(self, arguments, modulename=False, junitxml_file=False):
        super(JUnitXMLApplicationFactory, self).__init__(arguments=arguments)
        self.modulename = modulename
        self.junitxml_file = junitxml_file

    def _formatter(self):
        settings = self._settings(self.arguments)
        if settings.format == 'documentation':
            return formatters.DocumentationFormatter(settings)
        elif settings.format == 'junitxml':
            return JUnitXMLMambaFormatter(settings,
                                          modulename=self.modulename,
                                          junitxml_file=self.junitxml_file)
        else:
            return formatters.ProgressFormatter(settings)

    def _reporter(self):
        settings = self._settings(self.arguments)
        if settings.format == 'junitxml':
            return JUnitXMLMambaReporter(self._formatter())
        return super(JUnitXMLApplicationFactory, self)._reporter()


class JUnitXMLMambaReporter(reporter.Reporter):
    def create_report_suites(self):
        suites = []
        for listener in self.listeners:
            suites.append(listener.summary(
                self.duration, self.example_count,
                self.failed_count, self.pending_count))
        return suites


class JUnitXMLMambaFormatter(formatters.Formatter):
    def __init__(self, settings, modulename=False, junitxml_file=False):
        self.settings = settings
        self.result_file = junitxml_file
        self.junitxml_tests = {}
        self.junitxml_suites = False
        self.modulename = modulename
        self.current_group = False
        self.current_startedAt = False

    def _end_test(
            self, example, type='Passed', err_msg='', out_msg='', last=False
    ):
        if not last:
            last = self.current_startedAt
        self.current_startedAt = time.time()
        self.junitxml_tests[self.current_group]['tests'].append(
            junit_xml.TestCase(
                name=example.name,
                classname=self.current_group,
                status=type,
                elapsed_sec=self.current_startedAt - last,
                stderr=err_msg,
                stdout=out_msg
            )
        )

    def example_passed(self, example):
        self._end_test(example, type='Passed')

    def example_failed(self, example):
        self._end_test(example, type='Failed', err_msg=example.error.exception)

    def example_pending(self, example):
        self._end_test(example, type='Pending', out_msg='Skipped Example')

    def _start_test_group(self, example_group):
        self.current_startedAt = time.time()
        if not self.current_group:
            self.junitxml_tests['Total'] = {
                'startedAt': self.current_startedAt,
                'tests': [],
                'pre_group': False
            }
            self.current_group = 'Total'
        if example_group.name not in self.junitxml_tests.keys():
            self.junitxml_tests[example_group.name] = {
                'startedAt': self.current_startedAt,
                'tests': [],
                'pre_group': self.current_group or False
            }
        self.current_group = example_group.name

    def example_group_started(self, example_group):
        self._start_test_group(example_group)

    def example_group_finished(self, example_group):
        self.current_group = self.junitxml_tests[example_group.name].get(
            'pre_group', False) or 'Total'
        self._end_test(
            example_group, out_msg='Passed Group',
            last=self.junitxml_tests[example_group.name]['startedAt']
        )

    def example_group_pending(self, example_group):
        self._start_test_group(example_group)
        self.current_group = self.junitxml_tests[example_group.name].get(
            'pre_group', False) or 'Total'
        self._end_test(
            example_group, type='Pending', out_msg='Skipped Group',
            last=self.junitxml_tests[example_group.name]['startedAt']
        )

    def summary(self, duration, example_count, failed_count, pending_count):
        all_tests = []
        for testgroup in self.junitxml_tests.keys():
            for test in self.junitxml_tests[testgroup]['tests']:
                all_tests.append(test)
        return junit_xml.TestSuite(
            name='{}.{}'.format('mamba', self.modulename),
            test_cases=all_tests
        )
