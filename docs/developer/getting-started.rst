Getting started
===============

Scitacean is developed using `uv <https://docs.astral.sh/uv/>`_ to manage Python,
dependencies, etc. (see also `Dependency management <./dependency-management.rst>`_)
and `Just <https://just.systems>`_ as a task runner.

Setting up
----------

Dependencies
~~~~~~~~~~~~

- Install **uv** using any of the methods described
  `here <https://docs.astral.sh/uv/getting-started/installation/>`_.

- You can install **Just** as described in its
  `documentation <https://just.systems/man/en/introduction.html>`_.
  Or as a uv tool using

  .. code-block:: shell

      uv tool install rust-just

- Optional: Install **pre-commit** to run the same lints and formatters as on CI.
  See the `documentation <https://pre-commit.com/#installation>`_ or use

  .. code-block:: shell

    uv tool install pre-commit --with pre-commit-uv

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
This can be done conveniently using `pre-commit <https://pre-commit.com/>`_:

.. code-block:: sh

    pre-commit install

Alternatively, most checks can also be run manually through ``just``.
Take a look at ``.pre-commit-config.yaml`` for a list of all checks.

Running tests
-------------

The tests can be run using

.. code-block:: sh

    just test

If you also want to run backend and SFTP tests (requires Docker), use

.. code-block:: sh

    just test-all

The ``test`` and ``test-all`` rules accept arbitrary parameters which are
passed on to ``pytest``.
E.g., filter tests by name and run 4 worker processes:

.. code-block:: sh

    just test -k <test_name> -n 4

The examples above automatically use the correct dependencies.
If you don't want to use ``just``, take a look at ``justfile`` and ``pyproject.toml``
to find the relevant commands.

Building the docs
-----------------

Build the documentation using

.. code-block:: sh

    just docs-build

This will build the documentation pages and store them in a folder called ``html``.

You can also automatically check the documentation using

.. code-block:: sh

    just docs

This takes longer but is recommended before committing changes.

Static type checking
--------------------

Run Mypy using

.. code-block:: sh

    just mypy

Linting the codebase
--------------------

Lint the codebase using

.. code-block:: sh

    just lint

This will run a number of static analysis tools.

Formatting the codebase
-----------------------

Run a number of formatters on the codebase using

.. code-block:: sh

    just format
