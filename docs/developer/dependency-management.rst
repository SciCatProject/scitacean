Dependency management
=====================

Scitacean is a library, so the package dependencies are never pinned.
But (correct) lower bounds are encouraged and individual versions can be excluded.
See, e.g., `Should You Use Upper Bound Version Constraints <https://iscinumpy.dev/post/bound-version-constraints/>`_ for an explanation.

Development dependencies [#0]_ are pinned to an exact version in order to ensure reproducibility.
This is done automatically by `uv <https://docs.astral.sh/uv/>`_ whenever ``pyproject.toml`` is updated.
Pins can be updated explicitly using

.. code-block:: bash

    just lock

.. rubric:: Footnotes

.. [#0] As opposed to dependencies of the deployed package that users need to install.
