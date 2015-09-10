def patch_root_logger():
    import logging
    if 'openerp' not in logging.Logger.manager.loggerDict:
        logger = logging.getLogger()
        logger.propagate = False
        print logging.Logger.manager.loggerDict
