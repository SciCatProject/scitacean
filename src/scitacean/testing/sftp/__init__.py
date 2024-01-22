# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
"""Helpers for running tests with an SFTP server.

This subpackage is primarily meant for testing
:class:`scitacean.testing.sftp.SFTPFileTransfer`.
But it can also be used to test downstream code that uses the SFTP file transfer.

The `pytest <https://docs.pytest.org>`_ fixtures in this package manage an SFTP server
running in a docker container on the local machine.
They, therefore, require docker to be installed and running.

Use the :func:`scitacean.testing.sftp.fixtures.sftp_fileserver`
fixture to manage the server and use
:func:`scitacean.testing.sftp.fixtures.sftp_access`
to get all required access parameters.
See below for examples.

Attention
---------
The fixtures support `pytest-xdist <https://pytest-xdist.readthedocs.io/en/latest/>`_
but only if all workers run on the local machine (the default).

It may still happen that tests fail due to the complexity of synchronizing start up
and shut down of the SFTP server between workers.

See Also
--------
`Testing <../../user-guide/testing.ipynb>`_ user guide.

Examples
--------
In order to test the SFTP file transfer directly, use the provided fixtures to
open a connection manually.
Here, requesting the ``require_sftp_fileserver`` fixture ensures that the server
is running during the test, or that the test gets skipped if SFTP tests are disabled.
Passing the ``connect`` argument as shown ensures that the file transfer
connects to the test server with the correct parameters.

.. code-block:: python

    from scitacean.transfer.sftp import SFTPFileTransfer

    def test_sftp_upload(
        sftp_access,
        sftp_connect_with_username_password,
        require_sftp_fileserver,
        sftp_data_dir,
    ):
        sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
        ds = Dataset(...)
        with sftp.connect_for_upload(
            dataset=ds,
            connect=sftp_connect_with_username_password
        ) as connection:
            # do upload
        # assert that the file has been copied to sftp_data_dir

Testing the SFTP transfer together with a client requires some additional setup.
See ``test_client_with_sftp`` in
`sftp_test.py <https://github.com/SciCatProject/scitacean/blob/main/tests/transfer/sftp_test.py>`_
for an example.

Implementation notes
--------------------
When the server fixture is first used, it initializes the server using these steps:

1. Create a temporary directory with contents::

       tmpdir
         ├ docker-compose.yaml
         ├ .env         (specifies paths for docker volumes)
         ├ counter      (number of workers currently using the server)
         ├ counter.lock (file lock)
         └ data         (storage of files)
            └ seed      (populated from scitacean/testing/sftp/sftp_server_seed)

2. Start docker.
3. Make data writable by the user in docker.
   This changes the ownership of data on the host to root (on some machines).

The docker container and its volumes are removed at the end of the tests.
The fixture also tries to remove the temporary directory.
This can fail as the owner of its contents (in particular data)
may have been changed to root.
So cleanup can fail and leave the directory behind.

Use the seed directory (``sftp_data_dir/"seed"``) to test downloads.
Corresponds to ``/data/seed`` on the server.

Use the base data directory (``sftp_data_dir``) to test uploads.
Corresponds to ``/data`` on the server.

The counter and counter.lock files are used to synchronize starting and stopping
of the docker container between processes.
This is required when ``pytest-xdist`` is used.
Otherwise, those files will not be present.
"""

from ._pytest_helpers import add_pytest_option, sftp_enabled, skip_if_not_sftp
from ._sftp import (
    IgnorePolicy,
    SFTPAccess,
    SFTPUser,
    configure,
    local_access,
    wait_until_sftp_server_is_live,
)

__all__ = [
    "add_pytest_option",
    "configure",
    "local_access",
    "sftp_enabled",
    "skip_if_not_sftp",
    "wait_until_sftp_server_is_live",
    "IgnorePolicy",
    "SFTPAccess",
    "SFTPUser",
]
