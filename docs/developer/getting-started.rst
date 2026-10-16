Getting started
===============

Scitacean is developed using `pixi <https://pixi.prefix.dev/>`_ to manage Python,
package dependencies, etc. (see also `Dependency management <./dependency-management.rst>`_).

Setting up
----------

Dependencies
~~~~~~~~~~~~

- Install **pixi** using any of the methods described
  `here <https://pixi.prefix.dev/latest/installation//>`_.

- Optional: Install **prek** to run the same linters and code formatters.
  See the `prek documentation <https://prek.j178.dev/installation/>`_ or use

  .. code-block:: shell

    pixi global install prek

- Install **Pandoc** with is required building the documentation.
  `pandoc <https://pandoc.org/>`_ is not on PyPI and needs to be
  installed through other means. (E.g. with your OS package manager.)

- Optional: If you want to run tests against a real backend or SFTP server, you also need
  `docker-compose <https://docs.docker.com/compose/>`_.
  See `Testing <./testing.rst>`_ for what this is good for and why.

Set up git hooks
~~~~~~~~~~~~~~~~

The CI pipeline runs a number of code formatting and static analysis tools.
If they fail, a build is rejected.
To avoid that, you can run the same tools locally.
This can be done conveniently using `prek <https://prek.j178.dev/>`_:

.. code-block:: sh

    prek install

Alternatively, most checks can also be run manually through ``pixi``.
Take a look at ``.pre-commit-config.yaml`` for a list of all checks.

Running tests
-------------

The tests can be run using

.. code-block:: sh

    pixi run test

If you also want to run backend and SFTP tests (requires Docker), use

.. code-block:: sh

    pixi test-all

The ``test`` and ``test-all`` tasks accept arbitrary parameters which are
passed on to ``pytest``.
E.g., filter tests by name and run 4 worker processes:

.. code-block:: sh

    pixi run test -k <test_name> -n 4

The examples above automatically use the correct dependencies.

Building the docs
-----------------

Build the documentation using

.. code-block:: sh

    pixi run docs

This will build the documentation pages and store them in a folder called ``html``.

You can also automatically check the documentation using

.. code-block:: sh

    pixi run docs-all

This takes longer but is recommended before committing changes.

Static type checking
--------------------

Run Mypy using

.. code-block:: sh

    pixi run mypy

Linting the codebase
--------------------

Lint the codebase using

.. code-block:: sh

    pixi run lint

This will run a number of static analysis tools.

Formatting the codebase
-----------------------

Run a number of formatters on the codebase using

.. code-block:: sh

    pixi run fmt
