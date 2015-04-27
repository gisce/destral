import logging
import time

from osconf import config_from_environment
from destral.utils import update_config


logger = logging.getLogger('destral.openerp')
DEFAULT_USER = 1


def patched_pool_jobs(*args, **kwargs):
    logger.debug('Patched ir.cron')
    return False


class OpenERPService(object):

    def __init__(self, **kwargs):
        config = config_from_environment('OPENERP', [], **kwargs)
        import netsvc
        import tools
        update_config(tools.config, **config)
        tools.config.parse()
        from tools import config as default_config
        self.config = update_config(default_config, **config)
        import pooler
        import workflow
        self.pooler = pooler
        self.db = None
        self.pool = None
        if 'db_name' in config:
            self.db_name = config['db_name']

    def create_database(self):
        db_name = 'test_' + str(int(time.time()))
        import sql_db
        conn = sql_db.db_connect('template1')
        cursor = conn.cursor()
        try:
            logger.info('Creating database %s', db_name)
            cursor.autocommit(True)
            cursor.execute('CREATE DATABASE ' + db_name + ' WITH TEMPLATE base')
            return db_name
        finally:
            cursor.close()

    def drop_database(self):
        import sql_db
        sql_db.close_db(self.db_name)
        conn = sql_db.db_connect('template1')
        cursor = conn.cursor()
        try:
            logger.info('Droping database %s', self.db_name)
            cursor.autocommit(True)
            cursor.execute('DROP DATABASE ' + self.db_name)
        finally:
            cursor.close()

    @property
    def db_name(self):
        return self.config['db_name']

    @db_name.setter
    def db_name(self, value):
        self.config['db_name'] = value
        self.db, self.pool = self.pooler.get_db_and_pool(self.db_name)
        logger.debug('Patching ir.cron _poolJobs with %s', patched_pool_jobs)
        cron = self.pool.get('ir.cron')
        cron._poolJobs = patched_pool_jobs
        self.pool.obj_pool['ir.cron'] = cron

    def install_module(self, module):
        logger.info('Installing module %s', module)
        import pooler
        from destral.transaction import Transaction
        module_obj = self.pool.get('ir.module.module')
        with Transaction().start(self.config['db_name']) as txn:
            module_obj.update_list(txn.cursor, txn.user)
            module_ids = module_obj.search(
                txn.cursor, DEFAULT_USER,
                [('name', '=', module)],
            )
            assert module_ids, "Module %s not found" % module
            module_obj.button_install(txn.cursor, DEFAULT_USER, module_ids)
            pool = pooler.get_pool(txn.cursor.dbname)
            mod_obj = pool.get('ir.module.module')
            ids = mod_obj.search(txn.cursor, txn.user, [
                ('state', 'in', ['to upgrade', 'to remove', 'to install'])
            ])
            unmet_packages = []
            mod_dep_obj = pool.get('ir.module.module.dependency')
            for mod in mod_obj.browse(txn.cursor, txn.user, ids):
                deps = mod_dep_obj.search(txn.cursor, txn.user, [
                    ('module_id', '=', mod.id)
                ])
                for dep_mod in mod_dep_obj.browse(txn.cursor, txn.user, deps):
                    if dep_mod.state in ('unknown', 'uninstalled'):
                        unmet_packages.append(dep_mod.name)
            mod_obj.download(txn.cursor, txn.user, ids)
            txn.cursor.commit()
        self.db, self.pool = pooler.restart_pool(
            self.config['db_name'], update_module=True
        )
