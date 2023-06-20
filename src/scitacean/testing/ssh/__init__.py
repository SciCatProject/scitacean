# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
"""Helpers for running tests with an SSH server.

This is primarily meant for testing ``SSHFileTransfer``.

Use the ``ssh_fileserver`` fixture to manage the server and use ``ssh_access`` to
get all required access parameters.
When the server fixture is first used, it initializes the server using these steps:

1. Create a temporary directory with contents
   tmpdir |
          |- docker-compose.yaml
          |- .env         (paths for docker volumes)
          |- counter      (number of workers using the server)
          |- counter.lock (file lock)
          |- data |       (storage of files)
                  |- seed (populated from scitacean.testing.ssh.ssh_server_seed)
2. Start docker.
3. Make data writable by the user in docker.
   This changes the ownership of data on the host to root (on some machines).

The docker container and its volumes are removed at the end of the tests.
The fixture also tries to remove the temporary directory.
This can fail as the owner of its contents (in particular data)
may have been changed to root.
So cleanup can fail and leave the directory behind.

Use the seed directory (``ssh_data_dir/"seed"``) to test downloads.
Corresponds to ``/data/seed`` on the server.

Use the base data directory (``ssh_data_dir``) to test uploads.
Corresponds to ``/data`` on the server.

The counter and counter.lock files are used to synchronize starting and stopping
of the docker container between processes.
This is required when ``pytest-xdist`` is used.
Otherwise, those files will not be present.
"""

from ._pytest_helpers import add_pytest_option, skip_if_not_ssh, ssh_enabled
from ._ssh import (
    IgnorePolicy,
    SSHAccess,
    SSHUser,
    can_connect,
    configure,
    local_access,
    wait_until_ssh_server_is_live,
)

__all__ = [
    "add_pytest_option",
    "can_connect",
    "configure",
    "local_access",
    "ssh_enabled",
    "skip_if_not_ssh",
    "wait_until_ssh_server_is_live",
    "IgnorePolicy",
    "SSHAccess",
    "SSHUser",
]
