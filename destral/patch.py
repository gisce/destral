import logging


logger = logging.getLogger(__name__)


def patch_root_logger():
    """Patch openerp server logging.
    """
    if 'openerp' not in logging.Logger.manager.loggerDict:
        logger = logging.getLogger()
        logger.handlers = []
        logging.basicConfig()


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

