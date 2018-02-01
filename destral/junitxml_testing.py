import unittest
import junit_xml
import time
import logging


class JUnitXMLResult(unittest.result.TestResult):
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        super(JUnitXMLResult, self).__init__(stream, descriptions, verbosity)
        self.junit_suite = False
        self.ran_tests = []
        self._time_tests = []
        self.modulename = False
        self.startedAt = None
        self.endedAt = None

    def startTestRun(self):
        self.startedAt = time.time()

    def printErrors(self):
        self.endedAt = time.time()
        self.junit_suite = junit_xml.TestSuite(
            name=self.modulename,
            test_cases=self.ran_tests
        )

    def startTest(self, test):
        self._time_tests.append({
            'start': time.time(),
            'end': False
        })
        if not self.modulename:
            self.modulename = str(test).split()[-1][1:-1]
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
        test_classname = self.modulename or 'destral'
        err_text = ''
        if err_data:
            err_text = self._exc_info_to_string(err_data, test)
        self.ran_tests.append(junit_xml.TestCase(
            name=test_name,
            classname=test_classname,
            elapsed_sec=(endtime - start_time),
            stdout=out_data,
            stderr=err_text,
            status=type
        ))

    def stopTest(self, test):
        self._end_test(test, type='Stopped')
        super(JUnitXMLResult, self).stopTest(test)

    def addError(self, test, err):
        self._end_test(test, err_data=err, type='Error')
        super(JUnitXMLResult, self).addError(test, err)

    def addFailure(self, test, err):
        self._end_test(test, err_data=err, type='Error')

    def addSuccess(self, test):
        self._end_test(test)

    def addSkip(self, test, reason):
        self._end_test(test, type='Skip', out_data=reason)


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
