Dependency management
=====================

Scitacean is a library, so the package dependencies are never pinned.
But lower bounds are fine and individual versions can be excluded.
See, e.g., `Should You Use Upper Bound Version Constraints <https://iscinumpy.dev/post/bound-version-constraints/>`_ for an explanation.

Development dependencies [#0]_ are pinned to an exact version in order to ensure reproducibility.
This is done by specifying packages and version constraints in ``requirements/*.in`` files and locking those dependencies using `pip-compile-multi <https://pip-compile-multi.readthedocs.io/en/latest/index.html>`_ to produce ``requirements/*.txt`` files.
Those files are then used by `tox <https://tox.wiki/en/latest/>`_ to create isolated environments and run tests, build docs, etc.

tox can be cumbersome to use for local development.
So ``requirements/dev.txt`` can be used to create a virtual environment with all dependencies.

.. rubric:: Footnotes

.. [#0] As opposed to dependencies of the deployed package that users need to install.
