Getting Started
===============

Setting Up
----------

Dependencies
~~~~~~~~~~~~

Development dependencies are specified in ``requirements/dev.txt`` and can be installed using (see `Dependency Management <./dependency-management.rst>`_ for more information)

.. code-block:: sh

    pip install -r requirements/dev.txt

Additionally, building the documentation requires `pandoc <https://pandoc.org/>`_ which is not on PyPI and needs to be installed through other means.
(E.g. with your OS pacakge manager.)

If you want to run tests against a real backend, you also need ``docker-compose``.
And the ``scicatlive`` git submodule needs to be initialized.
See `Testing <./testing.rst>`_ for what this is good for and why.

Install the Package
~~~~~~~~~~~~~~~~~~~

Install the package in editable mode using

.. code-block:: sh

    pip install -e .

Set Up Git Hooks
~~~~~~~~~~~~~~~~

The CI pipeline runs a number of code formatting and static analysis tools.
If they fail, a build is rejected.
To avoid that, you can run the same tools locally.
This can be done conveniently using `pre-commit <https://pre-commit.com/>`_:

.. code-block:: sh

    pre-commit install

Alternatively, if you want a different workflow, take a look at `tox.ini` or `.pre-commit.yaml` to see what tools are run and how.

Manual Setup
------------

Run the tests using

.. code-block:: sh

    pytest

Or to run tests against a real backend (see setup above)


.. code-block:: sh

    pytest --backend-tests

Note that the setup and teardown of the backend takes several seconds.

Build the documentation using

.. code-block:: sh

    python -m sphinx -v -b html -d build/.doctrees docs build/html

Additionally, test the documentation using

.. code-block:: sh

    python -m sphinx -v -b doctest -d build/.doctrees docs build/html
    python -m sphinx -v -b linkcheck -d build/.doctrees docs build/html


Using Tox
---------

Run the tests using (e.g. python 3.10)

.. code-block:: sh

    tox -e py310

Build the documentation using

.. code-block:: sh

    tox -e docs
