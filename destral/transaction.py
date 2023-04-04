from threading import local
import six


from destral.openerp import OpenERPService
from signals import DB_CURSOR_EXECUTE


class Singleton(type):
    """Metaclass for singleton pattern.

    :copyright: Tryton Project
    """
    def __init__(mcs, name, bases, dict_):
        super(Singleton, mcs).__init__(name, bases, dict_)
        mcs.instance = None

    def __call__(mcs, *args, **kwargs):
        if mcs.instance is None:
            mcs.instance = super(Singleton, mcs).__call__(*args, **kwargs)
        return mcs.instance


@six.add_metaclass(Singleton)
class Transaction(local):
    """Transaction object
    """

    database = None
    service = None
    pool = None
    cursor = None
    user = None
    context = None

    def __init__(self):
        pass

    def start(self, database_name, user=1, context=None):
        """Start a new transaction

        :param database_name: Database name
        :param user: User id
        :param context: Context to be used
        """
        self._assert_stopped()
        self.service = OpenERPService(db_name=database_name)
        self.pool = self.service.pool
        self.cursor = self.service.db.cursor()
        self.user = user
        try:
            receivers = DB_CURSOR_EXECUTE.receivers
            DB_CURSOR_EXECUTE.receivers = {}
            self.context = context if context is not None else self.get_context()
        finally:
            DB_CURSOR_EXECUTE.receivers = receivers
        return self

    def stop(self):
        """Stop the transaction.
        """
        if self.cursor is not None:
            self.cursor.close()
        self.service = None
        self.cursor = None
        self.user = None
        self.context = None
        self.database = None
        self.pool = None

    def get_context(self):
        """Loads the context of the current user
        """
        assert self.user is not None

        user_obj = self.pool.get('res.users')
        return user_obj.context_get(self.cursor, self.user)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

    def _assert_stopped(self, deep=False):
        try:
            assert self.service is None
            assert self.database is None
            assert self.cursor is None
            assert self.pool is None
            assert self.user is None
            assert self.context is None
        except AssertionError as ae:
            if not deep:
                self.stop()
                return self._assert_stopped(True)
            raise ae
