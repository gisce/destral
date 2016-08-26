# coding=utf-8
from __future__ import absolute_import
import logging

from coverage import Coverage, CoverageException

logger = logging.getLogger('destral.coverage')


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

    def report(self, *args, **kwargs):
        if self.enabled:
            try:
                return super(OOCoverage, self).report(*args, **kwargs)
            except CoverageException as e:
                logger.error(e)
                return None
