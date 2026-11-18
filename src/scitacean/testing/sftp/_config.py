# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
import io
from dataclasses import dataclass
from typing import Any

import paramiko

from .._services import assets
from .._services.config import SFTP_PORT


@dataclass
class SFTPUser:
    username: str
    password: str

    @staticmethod
    def private_key() -> paramiko.PKey:
        """Return a valid private SSH key."""
        return paramiko.Ed25519Key.from_private_key(
            io.StringIO(assets.ssh_private_key())
        )


@dataclass
class SFTPAccess:
    host: str
    port: int
    user: SFTPUser


def local_access() -> SFTPAccess:
    config = assets.docker_compose_template()
    service = config["services"]["sftp"]
    env = dict(map(lambda s: s.split("="), service["environment"]))
    return SFTPAccess(
        host="localhost",
        port=SFTP_PORT,
        user=SFTPUser(
            username=env["USER_NAME"],
            password=env["USER_PASSWORD"],
        ),
    )


def cleanup_data_dir(
    sftp_access: SFTPAccess, sftp_connect_with_username_password: Any
) -> None:
    # Delete all directories created by tests.
    # These are owned by root on the host and cannot be deleted by Python's tempfile.
    connection = sftp_connect_with_username_password(
        host=sftp_access.host, port=sftp_access.port
    )
    connection.run(
        "find /data -not -path '/data' -not -path '/data/seed' | xargs rm -rf",
        hide=True,
        in_stream=False,
    )


def _make_client(sftp_access: SFTPAccess) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(IgnorePolicy())
    client.connect(
        hostname=sftp_access.host,
        port=sftp_access.port,
        username=sftp_access.user.username,
        password=sftp_access.user.password,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


# Every time we create a container, it gets a new host key.
# So simply accept any host keys.
class IgnorePolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client: Any, hostname: Any, key: Any) -> None:
        return
