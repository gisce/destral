# coding=utf-8
import sys
import types
import unittest


previous_modules = {}


def set_fake_module(name, module):
    previous_modules.setdefault(name, sys.modules.get(name))
    sys.modules[name] = module


def tearDownModule():
    for name, module in list(previous_modules.items()):
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module
        previous_modules.pop(name, None)


class FakeCursor(object):

    def __init__(self):
        self.statements = []
        self.closed = False
        self.autocommit_enabled = False

    def autocommit(self, value):
        self.autocommit_enabled = value

    def execute(self, statement, params=None):
        self.statements.append((statement, params))

    def close(self):
        self.closed = True


class FakeConnection(object):

    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class FakeSqlDb(types.ModuleType):

    def __init__(self):
        types.ModuleType.__init__(self, 'sql_db')
        self.Connection = object
        self.cursor = FakeCursor()
        self.closed = []
        self.connected = []

    def db_connect(self, db_name):
        self.connected.append(db_name)
        return FakeConnection(self.cursor)

    def close_db(self, db_name):
        self.closed.append(db_name)


try:
    import typing  # noqa
except ImportError:
    fake_typing = types.ModuleType('typing')
    fake_typing.Optional = object
    set_fake_module('typing', fake_typing)

fake_sql_db = FakeSqlDb()
set_fake_module('sql_db', fake_sql_db)

fake_osconf = types.ModuleType('osconf')
fake_osconf.config_from_environment = lambda *args, **kwargs: kwargs
set_fake_module('osconf', fake_osconf)

fake_psycopg2 = types.ModuleType('psycopg2')
fake_psycopg2.OperationalError = Exception
set_fake_module('psycopg2', fake_psycopg2)

fake_osv = types.ModuleType('osv')
fake_osv_osv = types.ModuleType('osv.osv')
fake_osv_osv.osv_pool = object
set_fake_module('osv', fake_osv)
set_fake_module('osv.osv', fake_osv_osv)

from destral import openerp
tearDownModule()


class DatabaseNameTests(unittest.TestCase):

    def setUp(self):
        self.previous_sql_db = sys.modules.get('sql_db')
        sys.modules['sql_db'] = fake_sql_db
        fake_sql_db.cursor = FakeCursor()
        fake_sql_db.closed = []
        fake_sql_db.connected = []

    def tearDown(self):
        if self.previous_sql_db is None:
            sys.modules.pop('sql_db', None)
        else:
            sys.modules['sql_db'] = self.previous_sql_db

    def test_generate_database_name_uses_safe_unique_prefix(self):
        db_name = openerp.generate_database_name()

        self.assertTrue(db_name.startswith('test_'))
        self.assertEqual(openerp.validate_database_name(db_name), db_name)
        self.assertLessEqual(len(db_name), openerp.POSTGRES_IDENTIFIER_MAX_LENGTH)

    def test_validate_database_name_accepts_postgres_identifier_subset(self):
        self.assertEqual(openerp.validate_database_name('test_database_1'), 'test_database_1')

    def test_validate_database_name_rejects_unsafe_names(self):
        unsafe_names = [
            '',
            '1test',
            'test-db',
            'test db',
            'test;DROP_DATABASE_postgres',
            'test"quote',
            'a' * (openerp.POSTGRES_IDENTIFIER_MAX_LENGTH + 1),
        ]
        for db_name in unsafe_names:
            with self.assertRaises(ValueError):
                openerp.validate_database_name(db_name)

    def test_create_database_quotes_database_identifier(self):
        service = object.__new__(openerp.OpenERPService)

        result = service.create_database(template=False, db_name='test_database')

        self.assertEqual(result, 'test_database')
        self.assertEqual(fake_sql_db.connected, ['postgres'])
        self.assertEqual(fake_sql_db.closed, ['postgres'])
        self.assertEqual(
            fake_sql_db.cursor.statements,
            [('CREATE DATABASE "test_database"', None)]
        )

    def test_create_database_with_template_quotes_identifiers(self):
        service = object.__new__(openerp.OpenERPService)

        service.create_database(template=True, db_name='test_database')

        self.assertEqual(
            fake_sql_db.cursor.statements,
            [('CREATE DATABASE "test_database" WITH TEMPLATE "base"', None)]
        )

    def test_create_database_rejects_unsafe_name_before_connecting(self):
        service = object.__new__(openerp.OpenERPService)

        with self.assertRaises(ValueError):
            service.create_database(template=False, db_name='test;DROP_DATABASE_postgres')

        self.assertEqual(fake_sql_db.connected, [])

    def test_drop_database_quotes_identifier_and_uses_parameter_for_datname(self):
        service = object.__new__(openerp.OpenERPService)
        service.config = {'db_name': 'test_database'}

        service.drop_database()

        self.assertEqual(fake_sql_db.connected, ['template1'])
        self.assertEqual(fake_sql_db.closed, ['test_database'])
        self.assertEqual(
            fake_sql_db.cursor.statements,
            [
                (
                    "SELECT pg_terminate_backend(pg_stat_activity.pid) "
                    " FROM pg_stat_activity "
                    " WHERE pg_stat_activity.datname = %s"
                    " AND pid <> pg_backend_pid() ",
                    ('test_database',)
                ),
                ('DROP DATABASE "test_database"', None),
            ]
        )

    def test_db_name_setter_rejects_unsafe_names(self):
        service = object.__new__(openerp.OpenERPService)
        service.config = {}

        with self.assertRaises(ValueError):
            service.db_name = 'test;DROP_DATABASE_postgres'


if __name__ == '__main__':
    unittest.main()
