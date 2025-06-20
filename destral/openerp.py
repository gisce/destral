import logging
import time

from osconf import config_from_environment
from typing import Optional

from destral.utils import update_config
import psycopg2

from osv.osv import osv_pool
from sql_db import Connection

logger = logging.getLogger('destral.openerp')
DEFAULT_USER = 1
"""Default user id
"""


def patched_pool_jobs(*args, **kwargs):
    """Patch pool jobs
    """
    logger.debug('Patched ir.cron')
    return False


class OpenERPService(object):
    """OpenERP Service.
    """

    def __init__(self, **kwargs):
        """Creates a new OpenERP service.

        :param \**kwargs: keyword arguments passed to the config
        """
        config = config_from_environment('OPENERP', [], **kwargs)
        import service
        import netsvc
        import tools
        update_config(tools.config, **config)
        if hasattr(tools.config, 'parse'):
            tools.config.parse()
        from tools import config as default_config
        from ctx import _cursor_context, _ws_info
        self.config = update_config(default_config, **config)
        import pooler
        import workflow
        self.pooler = pooler
        self.db = None  # type: Optional[Connection]
        self.pool = None    # type: Optional[osv_pool]
        self.cursor_stack = _cursor_context
        self.ws_stack = _ws_info
        if 'db_name' in config:
            try:
                self.db_name = config['db_name']
            except psycopg2.OperationalError as e:
                logger.info(
                    "Error opening named database '%s', creating it",
                    config['db_name'])
                self.db_name = self.create_database(False, db_name=config['db_name'])
        # Stop the cron
        netsvc.Agent.quit()

    def create_database(self, template=True, db_name=None):
        """Creates a new database.

        :param template: use a template (name must be `base`) (default True)
        """
        if db_name is None:
            db_name = 'test_' + str(int(time.time()))
        import sql_db
        conn = sql_db.db_connect('postgres')
        cursor = conn.cursor()
        try:
            logger.info('Creating database %s', db_name)
            cursor.autocommit(True)
            if template:
                cursor.execute('CREATE DATABASE {} WITH TEMPLATE base'.format(
                    db_name
                ))
            else:
                cursor.execute('CREATE DATABASE {}'.format(db_name))
            return db_name
        finally:
            cursor.close()
            sql_db.close_db('postgres')

    def drop_database(self):
        """Drop database from `self.db_name`
        """
        import sql_db
        sql_db.close_db(self.db_name)
        conn = sql_db.db_connect('template1')
        cursor = conn.cursor()
        try:
            logger.info('Droping database %s', self.db_name)
            cursor.autocommit(True)
            logger.info('Disconnect all sessions from database %s', self.db_name)
            cursor.execute(
                "SELECT pg_terminate_backend(pg_stat_activity.pid) "
                " FROM pg_stat_activity "
                " WHERE pg_stat_activity.datname = '{}'"
                " AND pid <> pg_backend_pid() ".format(self.db_name)
            )
            cursor.execute('DROP DATABASE ' + self.db_name)
        finally:
            cursor.close()

    @property
    def db_name(self):
        """Database name.
        """
        return self.config['db_name']

    @db_name.setter
    def db_name(self, value):
        self.config['db_name'] = value
        if value:
            self.db, self.pool = self.pooler.get_db_and_pool(self.db_name)
        else:
            self.db = None
            self.pool = None

    def install_module(self, module, with_test_depends=False):
        """Installs a module

        :param module: Module to install
        """
        logger.info('Installing module %s', module)
        import pooler
        from destral.transaction import Transaction
        module_obj = self.pool.get('ir.module.module')
        with Transaction().start(self.config['db_name']) as txn:
            cursor = txn.cursor
            uid = txn.user
            module_ids = module_obj.search(cursor, uid, [
                ('name', '=', module),
                ('state', '=', 'installed')
            ])
            if not module_ids:
                module_obj.update_list(cursor, uid)
                module_ids = module_obj.search(
                    txn.cursor, DEFAULT_USER,
                    [('name', '=', module)],
                )
                assert module_ids, "Module %s not found" % module
                module_info = module_obj.get_module_info(module)
                if with_test_depends and module_info.get('test_depends'):
                    logger.info("Found extra dependencies for module %s" % module)
                    extra_modules = module_info['test_depends']
                    logger.info("Including extra dependencies:\n%s" % '\n'.join(extra_modules))
                    extra_modules_ids = module_obj.search(
                        txn.cursor, DEFAULT_USER,
                        [('name', 'in', extra_modules), ('state', '!=', 'installed')],
                    )
                    if len(extra_modules_ids) != len(extra_modules):
                        logger.warning("Some extra dependencies were not found or already installed")

                    module_ids.extend(extra_modules_ids)

                module_obj.button_install(cursor, uid, module_ids)
                pool = pooler.get_pool(cursor.dbname)
                mod_obj = pool.get('ir.module.module')
                ids = mod_obj.search(cursor, uid, [
                    ('state', 'in', ['to upgrade', 'to remove', 'to install'])
                ])
                unmet_packages = []
                mod_dep_obj = pool.get('ir.module.module.dependency')
                for mod in mod_obj.browse(cursor, uid, ids):
                    deps = mod_dep_obj.search(cursor, uid, [
                        ('module_id', '=', mod.id)
                    ])
                    for dep_mod in mod_dep_obj.browse(cursor, uid, deps):
                        if dep_mod.state in ('unknown', 'uninstalled'):
                            unmet_packages.append(dep_mod.name)
                mod_obj.download(cursor, uid, ids)
                cursor.commit()
        try:
            self.db, self.pool = pooler.restart_pool(
                self.config['db_name'], update_module=True
            )
        except Exception:
            self.shutdown(1)
            raise

    def enable_admin(self, password='admin'):
        from destral.transaction import Transaction
        with Transaction().start(self.config['db_name']) as txn:
            user_obj = self.pool.get('res.users')
            user_ids = user_obj.search(txn.cursor, txn.user, [
                ('login', '=', 'admin'),
                ('password', '=', False)
            ], context={'active_test': False})
            if user_ids:
                user_obj.write(txn.cursor, txn.user, user_ids, {
                    'active': True,
                    'password': password
                })
                txn.cursor.commit()
                logger.info(
                    'User admin enabled with password: %s on %s',
                    password, txn.cursor.dbname)

    def shutdown(self, return_code):
        try:
            from signals import SHUTDOWN_REQUEST
            SHUTDOWN_REQUEST.send(exit_code=return_code)
        except TypeError:
            # Backwards compatible
            logger.warning('Old SHUTDOWN signal API withoud return_code')
            SHUTDOWN_REQUEST.send(None)
        except ImportError:
            pass
