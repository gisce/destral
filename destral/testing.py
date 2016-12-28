import importlib
import logging
import os
import unittest

from destral.openerp import OpenERPService
from destral.transaction import Transaction
from destral.utils import module_exists
from osconf import config_from_environment
from mamba import application_factory


logger = logging.getLogger('destral.testing')


class OOTestSuite(unittest.TestSuite):

    def __init__(self, tests=()):
        super(OOTestSuite, self).__init__(tests)
        self.config = config_from_environment(
            'DESTRAL', ['module'], use_template=True
        )
        ooconfig = {}
        self.config['use_template'] = False
        ooconfig['demo'] = {'all': 1}
        if self.config['module'] == 'base':
            ooconfig.setdefault('update', {})
            ooconfig['update'].update({'base': 1})
        self.openerp = OpenERPService(**ooconfig)
        self.drop_database = True

    def run(self, result, debug=False):
        """Run the test suite

        * Sets the config using environment variables prefixed with `DESTRAL_`.
        * Creates a new OpenERP service.
        * Installs the module to test if a database is not defined.
        """
        module_suite = not result._testRunEntered
        if module_suite:
            if not self.openerp.db_name:
                self.openerp.db_name = self.openerp.create_database(
                    self.config['use_template']
                )
            else:
                self.drop_database = False
            result.db_name = self.openerp.db_name
            self.openerp.install_module(self.config['module'])
        else:
            self.openerp.db_name = result.db_name

        res = super(OOTestSuite, self).run(result, debug)

        module_suite = not result._testRunEntered
        if module_suite:
            if self.drop_database:
                self.openerp.drop_database()
                self.openerp.db_name = False
            else:
                logger.info('Not dropping database %s', self.openerp.db_name)
                self.openerp.enable_admin()
        return res

    def _handleClassSetUp(self, test, result):
        test_class = test.__class__
        test_class.openerp = self.openerp
        test_class.config = self.config
        super(OOTestSuite, self)._handleClassSetUp(test, result)


class OOTestLoader(unittest.TestLoader):
    suiteClass = OOTestSuite


class OOTestCase(unittest.TestCase):
    """Base class to inherit test cases from for OpenERP Testing Framework.
    """

    require_demo_data = False
    """Require demo data to run the tests.
    """

    @property
    def database(self):
        """Database used in the test.
        """
        return self.openerp.db_name


class OOBaseTests(OOTestCase):

    def test_all_views(self):
        """Tests all views defined in the module.
        """
        logger.info('Testing views for module %s', self.config['module'])
        imd_obj = self.openerp.pool.get('ir.model.data')
        view_obj = self.openerp.pool.get('ir.ui.view')
        with Transaction().start(self.database) as txn:
            imd_ids = imd_obj.search(txn.cursor, txn.user, [
                ('model', '=', 'ir.ui.view'),
                ('module', '=', self.config['module'])
            ])
            if imd_ids:
                views = {}
                for imd in imd_obj.read(txn.cursor, txn.user, imd_ids):
                    view_xml_name = '{}.{}'.format(imd['module'], imd['name'])
                    views[imd['res_id']] = view_xml_name
                view_ids = views.keys()
                logger.info('Testing %s views...', len(view_ids))
                for view in view_obj.browse(txn.cursor, txn.user, view_ids):
                    view_xml_name = views[view.id]
                    model = self.openerp.pool.get(view.model)
                    if model is None:
                        # Check if model exists
                        raise Exception(
                            'View (xml id: %s) references model %s which does '
                            'not exist' % (view_xml_name, view.model)
                        )
                    logger.info('Testing view %s (id: %s)', view.name, view.id)
                    model.fields_view_get(txn.cursor, txn.user, view.id,
                                          view.type)
                    if view.inherit_id:
                        while view.inherit_id:
                            view = view.inherit_id
                        model.fields_view_get(txn.cursor, txn.user, view.id,
                                              view.type)
                        logger.info('Testing main view %s (id: %s)',
                                    view.name, view.id)

    def test_access_rules(self):
        """Test access rules for all the models created in the module
        """
        logger.info('Testing access rules for module %s', self.config['module'])
        imd_obj = self.openerp.pool.get('ir.model.data')
        access_obj = self.openerp.pool.get('ir.model.access')
        no_access = []
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            imd_ids = imd_obj.search(txn.cursor, txn.user, [
                ('model', '=', 'ir.model'),
                ('module', '=', self.config['module'])
            ])
            if imd_ids:
                for imd in imd_obj.browse(txn.cursor, txn.user, imd_ids):
                    model_id = imd.res_id
                    access_ids = access_obj.search(cursor, uid, [
                        ('model_id.id', '=', model_id)
                    ])
                    if not access_ids:
                        no_access.append(
                            '.'.join(imd.name.split('_')[1:])
                        )

        if no_access:
            self.fail(
                "Models: {0} doesn't have any access rules defined".format(
                    ', '.join(no_access)
            ))


def get_unittest_suite(module, tests=None):
    """Get the unittest suit for a module
    """
    tests_module = '{}.tests'.format(module)
    logger.debug('Test module: %s', tests_module)
    if module_exists(tests_module) is None:
        importlib.import_module(tests_module)
    if tests:
        tests = ['{}.{}'.format(tests_module, t) for t in tests]
        suite = OOTestLoader().loadTestsFromNames(tests)
    else:
        try:
            suite = OOTestLoader().loadTestsFromName(tests_module)
            suite.addTests(OOTestLoader().loadTestsFromTestCase(OOBaseTests))
        except AttributeError as e:
            logger.debug('Test suits not found...%s', e)
            suite = OOTestSuite()
    if not suite.countTestCases():
        suite = OOTestLoader().loadTestsFromName('destral.testing')
    # Clean netsvc Services
    import netsvc
    netsvc.SERVICES.clear()
    from workflow.wkf_service import workflow_service
    workflow_service()
    return suite


def run_unittest_suite(suite):
    """Run test suite
    """
    logger.info('Running test suit: {0}'.format(suite))
    return unittest.TextTestRunner(verbosity=2).run(suite)


def get_spec_suite(module):
    """
    Get spec suite to run Mamba
    :param module: Module to get the spec suite
    :return: suite
    """
    spec_dir = os.path.join(module, 'spec')
    if os.path.exists(spec_dir):
        # Create a fake arguments object
        arguments = type('Arguments', (object, ), {})
        arguments.specs = [spec_dir]
        arguments.slow = 0.075
        arguments.enable_coverage = False
        arguments.format = 'progress'
        arguments.no_color = True
        arguments.watch = False
        factory = application_factory.ApplicationFactory(arguments)
        logger.info('Mamba application factory created for specs: {0}'.format(
            spec_dir
        ))
        return factory.create_runner()
    return None


def run_spec_suite(suite):
    """
    Run Spec suite
    :param suite: mamba Runner
    :return:
    """
    suite.run()
    return suite.reporter
