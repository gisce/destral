import logging
import sql_db


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


class PatchedConnection(sql_db.Connection):

    def __init__(self, pool, db_name, cursor):
        self._cursor = PatchedCursor(cursor)
        super(PatchedConnection, self).__init__(pool, db_name)

    def cursor(self, serialized=False):
        return self._cursor


class PatchNewCursors(object):

    @staticmethod
    def db_connect(db_name):
        from destral.transaction import Transaction
        cursor = Transaction().cursor
        return PatchedConnection(sql_db._Pool, db_name, cursor)

    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        import sql_db
        logger.info('Patching creation of new cursors')
        self.orig = sql_db.db_connect
        sql_db.db_connect = PatchNewCursors.db_connect

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info('Unpatching creation of new cursors')
        sql_db.db_connect = self.orig
