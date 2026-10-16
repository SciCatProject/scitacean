Dependency management
=====================

General
~~~~~~~

Scitacean is a library, so the package dependencies are never pinned.
But (correct) lower bounds are encouraged and individual versions can be excluded.
See, e.g., `Should You Use Upper Bound Version Constraints <https://iscinumpy.dev/post/bound-version-constraints/>`_ for an explanation.

Development dependencies [#0]_ are pinned to exact versions in order to ensure reproducibility.
This is done automatically by `pixi <https://pixi.prefix.dev/>`_ whenever ``pyproject.toml`` is updated.
Pins can be updated explicitly using

.. code-block:: bash

    pixi update

Linting and formatting
~~~~~~~~~~~~~~~~~~~~~~

Linters and formatters are managed as pre-commit hooks in ``.pre-commit-config.yaml``
using `prek <https://prek.j178.dev/installation/>`_.
When running linters or formatters through ``pixi``, e.g., ``pixi run fmt``,
``pixi`` will call ``prek`` internally.
This way, we can ensure that we always use the same tool versions on developer and CI machines.
You need to install ``prek`` separately, it is not provided by ``pixi``.

This means that linter versions are managed in ``.pre-commit-config.yaml``, _not_ ``pyproject.toml``.
To update them, run

.. code-block:: bash

    prek auto-update

.. rubric:: Footnotes

.. [#0] As opposed to dependencies of the deployed package that users need to install.
