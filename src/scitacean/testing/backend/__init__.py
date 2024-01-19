# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Utilities for running tests against a locally deployed SciCat backend.

This subpackage provides tools for using a real SciCat backend running in docker
containers on the local machine.
It, therefore, requires docker to be installed and running.
The package is in particular intended to be used with
`pytest <https://docs.pytest.org>`_ and the fixtures provided by the
:mod:`scitacean.testing.backend.fixtures` submodule.
But it is also possible to set up tests in a different way by using the functions
provided here.

Note
----
Although this package attempts to clean up after itself, it is possible that it
fails to tear down the backend completely if tests are aborted in an unusual way
(pressing Ctrl-C is fine).
If this happens, a running docker container may be left behind.
It needs to be stopped manually.
Failing this, future tests may freeze indefinitely during start up.

Attention
---------
The fixtures support `pytest-xdist <https://pytest-xdist.readthedocs.io/en/latest/>`_
but only if all workers run on the local machine (the default).

It may still happen that tests fail due to the complexity of synchronizing start up
and shut down of the backend between workers.

See Also
--------
`Testing <../../user-guide/testing.ipynb>`_ user guide.

Examples
--------
The following pytest test will download the "raw" dataset that is included in the seed.
It runs both with a real and a fake client.

.. code-block:: python

    from scitacean.testing.backend import seed

    def test_download(client):
        ds = client.get_dataset(seed.INITIAL_DATASETS["raw"].pid)
        # assert something

If a test requires a backend but wants to construct a client manually, use

.. code-block:: python

    def test_manual_client(require_scicat_backend, scicat_access):
        client = Client.from_credentials(
            url=scicat_access.url,
            **scicat_access.user.credentials
        )
        # assert something

.. rubric:: Functions

.. autosummary::
   :toctree: ../functions

   add_pytest_option
   backend_enabled
   configure
   skip_if_not_backend
   start_backend
   stop_backend
   wait_until_backend_is_live
"""

from . import config, seed
from ._backend import (
    configure,
    start_backend,
    stop_backend,
    wait_until_backend_is_live,
)
from ._pytest_helpers import add_pytest_option, backend_enabled, skip_if_not_backend

__all__ = [
    "add_pytest_option",
    "backend_enabled",
    "config",
    "configure",
    "seed",
    "skip_if_not_backend",
    "start_backend",
    "stop_backend",
    "wait_until_backend_is_live",
]
