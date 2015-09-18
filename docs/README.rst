.. include:: ../README.rst

Running tests
=============

To run your tests call `destral` from the command line. Options to the destral
command are::

  Usage: destral [OPTIONS]

    Options:
      -m, --modules TEXT
      -t, --tests TEXT
      --help              Show this message and exit.

where `-m` are the modules to be tested and `-t` the tests to run.

If no specific tests are definend into the module, *destral* will test:

  * Correct installation of the module.
  * All the views defined in the module are ok.


Configuring destral
===================

All the configuration can be made with environment variables with prefix
`DESTRAL_`