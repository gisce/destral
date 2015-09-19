def patch_root_logger():
    """Patch openerp server logging.
    """
    import logging
    if 'openerp' not in logging.Logger.manager.loggerDict:
        logger = logging.getLogger()
        logger.handlers = []
        logging.basicConfig()

