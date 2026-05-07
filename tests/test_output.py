# coding=utf-8
from __future__ import print_function

import os
import sys
import tempfile
import unittest

from destral.output import QuietOutputCapture


class QuietOutputCaptureTests(unittest.TestCase):

    def test_disabled_capture_does_not_create_log_file(self):
        capture = QuietOutputCapture(enabled=False)

        with capture:
            pass

        self.assertIsNone(capture.path)

    def test_enabled_capture_writes_stdout_and_stderr_to_file(self):
        capture = QuietOutputCapture(enabled=True, tail_lines=10)
        original_stdout_fd = os.dup(1)
        original_stderr_fd = os.dup(2)
        try:
            with capture:
                print('captured stdout')
                print('captured stderr', file=sys.stderr)

            self.assertIn('captured stdout', capture.tail())
            self.assertIn('captured stderr', capture.tail())
        finally:
            os.dup2(original_stdout_fd, 1)
            os.dup2(original_stderr_fd, 2)
            os.close(original_stdout_fd)
            os.close(original_stderr_fd)
            if capture.path and os.path.exists(capture.path):
                os.unlink(capture.path)

    def test_tail_limits_returned_lines(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            with open(path, 'w') as output_file:
                output_file.write('one\ntwo\nthree\n')
            capture = QuietOutputCapture(enabled=True, tail_lines=2)
            capture.path = path

            self.assertEqual(capture.tail(), 'two\nthree')
        finally:
            os.unlink(path)

    def test_cleanup_success_removes_capture_file(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        capture = QuietOutputCapture(enabled=True)
        capture.path = path

        capture.cleanup_success()

        self.assertFalse(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
