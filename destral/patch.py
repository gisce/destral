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


class PatchedCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def commit(self):
        return True

    def rollback(self, savepoint=False):
        return True

    def close(self):
        return True

    def __getattr__(self, item):
        return getattr(self.cursor, item)


class PatchedConnection(object):
    """Patched connection wapper to return the same cursor.

    This is useful when some method inside a testing mehtod creates new
    cursors.

    :param connection: Original connection
    :param cursor: Original cursor
    """

    def __init__(self, connection, cursor):
        self._connection = connection
        self._cursor = PatchedCursor(cursor)

    def __getattr__(self, item):
        return getattr(self._connection, item)

    def cursor(self, serialized=False):
        """Wrapped function to return the same cursor
        """
        return self._cursor


class PatchNewCursors(object):
    """Util to patch creation of new cursor.

    This will always return the cursor created by Transaction
    """

    @staticmethod
    def db_connect(db_name):
        from destral.transaction import Transaction
        import sql_db
        cursor = Transaction().cursor
        conn = sql_db.Connection(sql_db._Pool, db_name)
        return PatchedConnection(conn, cursor)

    def __enter__(self):
        import sql_db
        logger.info('Patching creation of new cursors')
        self.orig = sql_db.db_connect
        sql_db.db_connect = PatchNewCursors.db_connect

    def __exit__(self, exc_type, exc_val, exc_tb):
        import sql_db
        logger.info('Unpatching creation of new cursors')
        sql_db.db_connect = self.orig
