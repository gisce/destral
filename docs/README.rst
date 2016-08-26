.. include:: ../README.rst

Running tests
=============

To run your tests call `destral` from the command line. Options to the destral
command are::

  Usage: destral [OPTIONS]

    Options:
      --enable-coverage
      -m, --modules TEXT
      -t, --tests TEXT
      --help              Show this message and exit.

where `-m` are the modules to be tested and `-t` the tests to run. For the `-t`
parameter is needed to pass full test class and method. Eg: SomeTestClass.test_method

If no specific tests are defined into the module, *destral* will test:

  * Correct installation of the module.
  * All the views defined in the module are ok.
  * Definition of access rules for all the models of the module

If you have run with the `--enable-coverage` option a `.coverage` file will be
generated with the results and you can see the report executing::

  $ coverage report


Configuring destral
===================

All the configuration can be made with environment variables with prefix
`DESTRAL_`

Variables definition
--------------------

`DESTRAL_MODULE`:
  Module to test
`DESTRAL_USE_TEMPLATE`:
  If we want to use a template when creating a database for test, if this variable
  is set to `True` a database with name `base` must exists and will be used to
  create a temporally database for this test.

Configuring OpenERP
===================

All configuration for OpenERP server can be made with environment variables with
prefix `OPENERP_` and will overwrite the defaults in `tools.config`.

Useful variables
----------------

`OPENERP_DB_NAME`:
  A database to use, if this is set then the test framework assumes that the module
  is already installed and this database will not be deleted after the tests.
`OPENERP_UPDATE`:
  If you want to update some modules during the initialization of OpenERP service
  Eg value: `OPENERP_UPDATE={'base': 1, 'crm': 1}`

.. note::
  When developing is useful to have a database initialized and use `OPENERP_DB_NAME`
  variable to speed up the test.
