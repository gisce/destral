# coding=utf-8
"""Output helpers for destral command line execution."""
from __future__ import print_function

import os
import sys
import tempfile
from collections import deque


class QuietOutputCapture(object):
    """Capture stdout/stderr to a file and print a short failure summary.

    The implementation redirects file descriptors and Python stream objects so
    logging handlers, subprocesses and click test runners are captured. This
    keeps the default CLI behaviour untouched and makes quiet mode useful for
    automation that cannot afford very large terminal output.
    """

    def __init__(self, enabled=False, tail_lines=80):
        self.enabled = enabled
        self.tail_lines = tail_lines
        self.path = None
        self._fd = None
        self._stdout_fd = None
        self._stderr_fd = None
        self._stdout_stream = None
        self._stderr_stream = None
        self._stdout_proxy = None
        self._stderr_proxy = None

    def __enter__(self):
        if not self.enabled:
            return self
        fd, self.path = tempfile.mkstemp(
            prefix='destral-quiet-', suffix='.log'
        )
        self._fd = fd
        self._stdout_fd = os.dup(1)
        self._stderr_fd = os.dup(2)
        self._stdout_stream = sys.stdout
        self._stderr_stream = sys.stderr
        self._flush_standard_streams()
        os.dup2(self._fd, 1)
        os.dup2(self._fd, 2)
        self._stdout_proxy = os.fdopen(os.dup(self._fd), 'w')
        self._stderr_proxy = os.fdopen(os.dup(self._fd), 'w')
        sys.stdout = self._stdout_proxy
        sys.stderr = self._stderr_proxy
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.enabled:
            return False
        self.restore()
        return False

    def restore(self):
        if self._fd is None:
            return
        self._flush_standard_streams()
        if self._stdout_stream is not None:
            sys.stdout = self._stdout_stream
        if self._stderr_stream is not None:
            sys.stderr = self._stderr_stream
        self._close_proxy(self._stdout_proxy)
        self._close_proxy(self._stderr_proxy)
        os.dup2(self._stdout_fd, 1)
        os.dup2(self._stderr_fd, 2)
        os.close(self._stdout_fd)
        os.close(self._stderr_fd)
        os.close(self._fd)
        self._fd = None
        self._stdout_fd = None
        self._stderr_fd = None
        self._stdout_stream = None
        self._stderr_stream = None
        self._stdout_proxy = None
        self._stderr_proxy = None

    def cleanup_success(self):
        if self.enabled and self.path and os.path.exists(self.path):
            os.unlink(self.path)

    def emit_failure_summary(self, return_code=1):
        if not self.enabled:
            return
        print('destral failed with exit code {}'.format(return_code), file=sys.stderr)
        print('Full captured output: {}'.format(self.path), file=sys.stderr)
        tail = self.tail()
        if tail:
            print('', file=sys.stderr)
            print('Last {} captured lines:'.format(self.tail_lines), file=sys.stderr)
            print(tail, file=sys.stderr)

    def tail(self):
        if not self.path or not os.path.exists(self.path):
            return ''
        with open(self.path, 'rb') as output_file:
            tail_lines = deque(output_file, maxlen=self.tail_lines)
        if not tail_lines:
            return ''
        data = b''.join(tail_lines)
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = data.decode('utf-8', 'replace')
        return '\n'.join(text.splitlines())

    @staticmethod
    def _flush_standard_streams():
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except Exception:
                pass

    @staticmethod
    def _close_proxy(proxy):
        if proxy is None:
            return
        try:
            proxy.close()
        except Exception:
            pass
