# coding=utf-8
import unittest

from mock import Mock, patch

from destral import testing


class FakeOpenERP(object):
    db_name = 'test_db'


class FakeTransaction(object):

    def __init__(self, events):
        self.events = events
        self.cursor = 'cursor'
        self.user = 1

    def start(self, database):
        self.events.append(('start', database))
        return self

    def stop(self):
        self.events.append('stop')


class FakePatchNewCursors(object):

    def __init__(self, events):
        self.events = events

    def patch(self):
        self.events.append('patch')

    def unpatch(self):
        self.events.append('unpatch')


class FakeWsInfo(object):

    def __init__(self, events):
        self.events = events

    def push(self, tracker):
        self.events.append(('push', tracker))

    def pop(self):
        self.events.append('pop')


class CursorPatchTests(unittest.TestCase):

    def _run_case(self, case_class):
        events = []
        test_case = case_class(methodName='runTest')
        test_case.openerp = FakeOpenERP()
        transaction = FakeTransaction(events)
        cursor_patch = FakePatchNewCursors(events)
        tracker = Mock(name='tracker')

        with patch.object(testing, 'Transaction', return_value=transaction), \
                patch.object(testing, 'PatchNewCursors', return_value=cursor_patch), \
                patch.object(testing, '_ws_info', FakeWsInfo(events)), \
                patch.object(testing, 'WebServiceTracker', return_value=tracker):
            test_case.setUp()
            test_case.tearDown()

        return events, tracker

    def test_cursor_patching_is_disabled_by_default(self):
        class TestCase(testing.OOTestCaseWithCursor):
            def runTest(self):
                pass

        events, tracker = self._run_case(TestCase)

        self.assertEqual(
            events,
            [
                ('start', 'test_db'),
                ('push', tracker),
                'stop',
                'pop',
            ]
        )

    def test_cursor_patching_can_be_enabled_for_the_whole_test_class(self):
        class TestCase(testing.OOTestCaseWithCursor):
            _patch_cursors = True

            def runTest(self):
                pass

        events, tracker = self._run_case(TestCase)

        self.assertEqual(
            events,
            [
                ('start', 'test_db'),
                'patch',
                ('push', tracker),
                'unpatch',
                'stop',
                'pop',
            ]
        )


if __name__ == '__main__':
    unittest.main()
