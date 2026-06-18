Destral testing library
=======================

Destral provides an opinionated testing toolkit for the GISCE OpenERP v5 fork,
wrapping the ERP runtime so you can execute unit tests and behaviour specs
against your addons from the command line or continuous integration.

.. image:: https://badge.fury.io/py/destral.svg
    :target: https://badge.fury.io/py/destral

Overview
--------

* Test runner that discovers module unit tests and mamba specs.
* Coverage integration for server-wide or per-module reports.
* CLI helpers to provision databases, install addon requirements and generate
  JUnit XML for CI systems.
* Python 2.7 and 3.x compatible codebase validated in GitHub Actions.

Requirements
------------

* Python 2.7 **or** Python 3.8+ (GitHub Actions runs 3.11).
* The GISCE ERP fork cloned alongside this repository (``../erp``) so
  ``PYTHONPATH`` can include ``erp/server/bin``.
* Optional: the ``oorq`` addons repository for RQ integration tests.

Quick start
-----------

.. code-block:: console

   git clone https://github.com/gisce/destral.git
   git clone https://github.com/gisce/erp.git ../erp
   git clone https://github.com/gisce/oorq.git ../oorq
   cd destral
   python -m venv .venv && source .venv/bin/activate
   python -m pip install -e .
   python -m pip install -r requirements-dev.txt
   python -m pip install -r ../erp/requirements.txt

On Python 2.7 environments, pin ``pip<21`` and ``setuptools<45`` before
installing requirements.

Running tests
-------------

Unit tests live under ``tests/`` and cover Python helpers that do not depend on
OpenERP:

.. code-block:: console

   python -m unittest discover tests

Behaviour specs remain in ``spec/`` and rely on mamba. Ensure ``PYTHONPATH``
includes both the repository and the ERP server sources:

.. code-block:: console

   export PYTHONPATH=$(pwd):../erp/server/bin
   mamba spec

Use ``mamba spec -f documentation`` for verbose output. Both commands run in
CI, so keep them fast and deterministic.

Command line runner
-------------------

The ``destral`` CLI orchestrates module testing inside the ERP runtime:

.. code-block:: console

   destral --modules my_module --enable-coverage --report-junitxml reports/

Key options:

* ``--modules`` limits the run to specific addons.
* ``--enable-coverage`` / ``--report-coverage`` gather coverage metrics.
* ``--report-junitxml`` writes suites under the given directory.
* ``--requirements`` installs ``requirements*.txt`` for the addon and its
  dependencies before running specs and unit tests.

Continuous integration
----------------------

``.github/workflows/tests.yml`` runs the unit suite and mamba specs on pull
requests for Python 3.11 and Python 2.7 (via a ``python:2.7-slim`` container).
Provide the ``RO_GITHUB_ACTIONS_REPOS`` secret so the workflow can check out the
ERP and oorq repositories.

Contributing
------------

* Follow PEP 8 with 4-space indentation and keep lines under 100 characters.
* Maintain Python 2.7/3.x compatibility (prefer ``six``, avoid f-strings, guard
  type hints).
* Add regression specs whenever you touch CLI flows, coverage plumbing or ERP
  integration points.
* Run ``python -m pylint destral`` locally to catch regressions before opening a
  pull request.

.. epigraph::

   Code as if the next guy to maintain your code is a homicidal maniac who knows where you live.

   -- Kathy Sierra and Bert Bates
