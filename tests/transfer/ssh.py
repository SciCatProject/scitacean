# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

import paramiko
import pytest

from ..common.ssh_server import skip_if_not_ssh


@pytest.fixture(scope="session", autouse=True)
def server(request, ssh_fileserver):
    skip_if_not_ssh(request)


def test_asd(ssh_access):
    # with fabric.Connection(host=ssh_access.host,
    #                        port=ssh_access.port,
    #                        user=ssh_access.username,
    #                        connect_kwargs={'password': ssh_access.password}) as con:
    #     print(con.run('ls'))
    import logging

    from scitacean.logging import get_logger

    logger = get_logger()
    logger.setLevel(logging.DEBUG)
    hdlr = logging.StreamHandler()
    hdlr.setLevel(logging.DEBUG)
    logger.addHandler(hdlr)

    client = paramiko.SSHClient()
    client.connect("localhost", port=2222, username="user", password="password")
