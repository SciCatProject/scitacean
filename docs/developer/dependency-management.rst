Dependency management
=====================

General
~~~~~~~

Scitacean is a library, so the package dependencies are never pinned.
But (correct) lower bounds are encouraged and individual versions can be excluded.
See, e.g., `Should You Use Upper Bound Version Constraints <https://iscinumpy.dev/post/bound-version-constraints/>`_ for an explanation.

Development dependencies [#0]_ are pinned to an exact version in order to ensure reproducibility.
This is done automatically by `uv <https://docs.astral.sh/uv/>`_ whenever ``pyproject.toml`` is updated.
Pins can be updated explicitly using

.. code-block:: bash

    just update-deps

or with uv:

.. code-block:: bash

    uv lock --upgrade

Linting and formatting
~~~~~~~~~~~~~~~~~~~~~~

Linters and formatters are managed as pre-commit hooks in ``.pre-commit-config.yaml``
using `prek <https://prek.j178.dev/installation/>`_.
When running linters or formatters through ``just``, e.g., ``just format``,
``just`` will call ``prek`` internally.
This way, we can ensure that we always use the same tool versions on developer and CI machines.

This means that linter versions are managed in ``.pre-commit-config.yaml``, _not_ ``pyproject.toml``.
To update them, run

.. code-block:: bash

    prek auto-update

.. note::
    An earlier version implemented linters and formatters in ``justfile`` with
    ``uv run ...`` commands and managed tool versions in dependency groups.
    ``prek`` then called, e.g., ``just format``.
    This did not work well because it depends on ``just`` and ``uv`` to be visible on the ``PATH``
    of the shell that does the commit and this is not always the case (e.g., in PyCharm).

.. rubric:: Footnotes

.. [#0] As opposed to dependencies of the deployed package that users need to install.
