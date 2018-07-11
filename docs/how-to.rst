How to write a test
===================

Unittesting
-----------

Destral checks for a module called `tests` inside the module folder eg. `module/tests/__init__.py`.


.. code-block:: python

    from destral import testing
    from destral.transaction import Transaction

    class TestSimpleMethod(testing.OOTestCase):

        def setUp(self):
            self.txn = Transaction().start(self.database)
            self.cursor = self.txn.cursor()
            self.uid = self.txn.user

        def tearDown(self):
            self.txn.stop()

        def test_check_hello_world_name(self):
            obj = self.openerp.pool.get('our.object')
            self.assertEqual(
                obj.hello(self.cursor, self.uid, 'Pepito'),
                'Hello World Pepito!'
            )

.. versionadded:: v1.4.0

We can also use the `OOTestCaseWithCursor` class that already has the` setUp` and
`tearDown` made.
