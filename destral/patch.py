import logging


logger = logging.getLogger(__name__)


class RestorePatchedRegisterAll(object):
    def __enter__(self):
        import report

        logger.info('Saving original register_all {0}'.format(
            id(report.interface.register_all)
        ))
        self.orig = report.interface.register_all
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import report
        if id(report.interface.register_all) != id(self.orig):
            logger.info('Restoring register_all {0} to {1}'.format(
                id(report.interface.register_all), id(self.orig)
            ))
            report.interface.register_all = self.orig

