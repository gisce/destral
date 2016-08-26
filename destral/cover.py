# coding=utf-8
from __future__ import absolute_import

from coverage import Coverage


class OOCoverage(Coverage):
    def __init__(self, *args, **kwargs):
        self.enabled = True
        super(OOCoverage, self).__init__(*args, **kwargs)

    def start(self):
        if self.enabled:
            super(OOCoverage, self).start()

    def stop(self):
        if self.enabled:
            super(OOCoverage, self).stop()
