import logging
import functools
from ctx import current_session, current_cursor


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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return


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

    def cursor(self, serialized=False, *args, **kwargs):
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

    def patch(self):
        """
        Patch the database connection to always return the same cursor.

        This method replaces the `sql_db.db_connect` function with a custom
        implementation that returns a `PatchedConnection`. It also updates
        the current session's database connection to use the same patched
        connection. This ensures that all new cursors created during the
        session are consistent and tied to the same transaction.
        """
        import sql_db
        logger.info('Patching creation of new cursors')
        self.orig = sql_db.db_connect
        sql_db.db_connect = PatchNewCursors.db_connect
        self.orig_db = current_session.db
        current_session.db = PatchedConnection(current_session.db, current_cursor)

    def unpatch(self):
        """
        Restore the original database connection and cursor behavior.

        This method undoes the changes made by the `patch` method by:
        - Restoring the original `sql_db.db_connect` function.
        - Reverting `current_session.db` to its original state.
        """
        import sql_db
        logger.info('Unpatching creation of new cursors')
        sql_db.db_connect = self.orig
        current_session.db = self.orig_db

    def __enter__(self):
        self.patch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unpatch()
        return False
    def __call__(self, func):
        """Allow usage as a decorator"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.patch()
            try:
                return func(*args, **kwargs)
            finally:
                self.unpatch()
        return wrapper
