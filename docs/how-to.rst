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

Patching new cursors
~~~~~~~~~~~~~~~~~~~~

When testing methods that create new cursors internally (e.g., using `sql_db.db_connect`),
you can use the `PatchNewCursors` decorator to ensure all cursors point to the same
transaction cursor:

.. code-block:: python

    from destral import testing
    from destral.patch import PatchNewCursors
    from destral.transaction import Transaction

    class TestWithNewCursors(testing.OOTestCase):

        def setUp(self):
            self.txn = Transaction().start(self.database)
            self.cursor = self.txn.cursor
            self.uid = self.txn.user

        def tearDown(self):
            self.txn.stop()

        @PatchNewCursors()
        def test_method_that_creates_cursors(self):
            obj = self.openerp.pool.get('our.object')
            # This method internally creates new cursors
            # but they will all point to self.cursor
            obj.method_with_new_cursor(self.cursor, self.uid)

If all test methods in a test class need cursor patching, you can set the
`all_patched_cursors` class attribute to `True`:

.. code-block:: python

    from destral import testing
    from destral.transaction import Transaction

    class TestWithAllPatchedCursors(testing.OOTestCase):
        all_patched_cursors = True

        def setUp(self):
            self.txn = Transaction().start(self.database)
            self.cursor = self.txn.cursor
            self.uid = self.txn.user

        def tearDown(self):
            self.txn.stop()

        def test_method_one(self):
            # Automatically decorated with PatchNewCursors
            obj = self.openerp.pool.get('our.object')
            obj.method_with_new_cursor(self.cursor, self.uid)

        def test_method_two(self):
            # Also automatically decorated with PatchNewCursors
            obj = self.openerp.pool.get('another.object')
            obj.another_method_with_cursor(self.cursor, self.uid)
