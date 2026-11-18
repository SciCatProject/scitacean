# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Pytest plugin for SFTP tests with Scitacean."""

from collections.abc import Callable
from pathlib import Path

import pytest
from paramiko import SFTPClient, SSHClient

from .._logging import get_logger
from .._services.config import SFTP_DATA_DIR_NAME
from .._services.docker import DockerComposeProject
from ._config import (
    IgnorePolicy,
    SFTPAccess,
    local_access,
)

pytest_plugins = ("scitacean.testing._pytest_plugin",)

COMMAND_LINE_OPTION = "--sftp-tests"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add a command-line option to pytest to toggle SFTP tests."""
    parser.addoption(
        COMMAND_LINE_OPTION,
        action="store_true",
        default=False,
        help="Select whether to run tests with an SFTP fileserver",
    )


@pytest.fixture(scope="session")
def sftp_access(request: pytest.FixtureRequest) -> SFTPAccess:
    """Fixture that returns SFTP access parameters.

    Returns
    -------
    :
        A URL and user to connect to the testing SFTP server.
        The user has access to all initial files registered in the
        database and permissions to create new files.
    """
    _skip_if_not_sftp(request)
    return local_access()


@pytest.fixture(scope="session")
def sftp_data_dir(
    request: pytest.FixtureRequest,
    docker_project: DockerComposeProject,
) -> Path | None:
    """Fixture that returns the data directory for the SFTP server setup.

    Returns
    -------
    :
        A path to a directory on the host machine.
        The directory is mounted as ``/data`` on the server.

        Returns ``None`` if SFTP tests are disabled
    """
    if not _sftp_enabled(request):
        return None
    return docker_project.path.joinpath(SFTP_DATA_DIR_NAME)


@pytest.fixture(scope="session")
def sftp_connect_with_username_password(
    sftp_access: SFTPAccess,
) -> Callable[[str, int], SFTPClient]:
    """Fixture that returns a function to connect to the testing SFTP server.

    Uses username+password from the test config.

    Returns
    -------
    :
        A function to pass as the ``connect`` argument when constructing a
        :class:`scitacean.transfer.sftp.SFTPFileTransfer`.

    Examples
    --------
    Explicitly connect to the test server:

    .. code-block:: python

        def test_sftp(sftp_access,
                      sftp_connect_with_username_password,
                      sftp_fileserver):
            sftp = SFTPFileTransfer(host=sftp_access.host,
                                    port=sftp_access.port,
                                    connect=sftp_connect_with_username_password)
            with sftp.connect_for_download() as connection:
                # use connection
    """

    def connect(host: str, port: int) -> SFTPClient:
        client = SSHClient()
        client.set_missing_host_key_policy(IgnorePolicy())
        client.connect(
            hostname=host,
            port=port,
            username=sftp_access.user.username,
            password=sftp_access.user.password,
            allow_agent=False,
            look_for_keys=False,
        )
        return client.open_sftp()

    return connect


@pytest.fixture(scope="session")
def sftp_fileserver(
    request: pytest.FixtureRequest,
    docker_project: DockerComposeProject,
) -> bool:
    """Fixture to declare that a test needs a local SFTP server.

    If SFTP tests are enabled, this fixture configures and starts an SFTP server
    in a docker container the first time a test requests it.
    The server and container will be stopped and removed at the end of the test session.

    Does nothing if the SFTP tests are disabled.

    Returns
    -------
    :
        True if SFTP tests are enabled and False otherwise.
    """
    if not _sftp_enabled(request):
        return False

    get_logger().info("Preparing SFTP server")
    docker_project.ensure_running("sftp")
    return True


@pytest.fixture
def require_sftp_fileserver(
    request: pytest.FixtureRequest, sftp_fileserver: bool
) -> None:
    """Fixture to declare that a test needs a local SFTP server.

    Like :func:`scitacean.testing.sftp.pytest_plugin.sftp_fileserver`
    but this skips the test if SFTP tests are disabled.
    """
    _skip_if_not_sftp(request)


def _skip_if_not_sftp(request: pytest.FixtureRequest) -> None:
    """Mark the current test to be skipped if SFTP tests are disabled."""
    if not _sftp_enabled(request):
        pytest.skip(
            "Tests against an SFTP file server are disabled, "
            f"use {COMMAND_LINE_OPTION} to enable them"
        )


def _sftp_enabled(request: pytest.FixtureRequest) -> bool:
    """Return True if SFTP tests are enabled."""
    return COMMAND_LINE_OPTION is not None and bool(
        request.config.getoption(COMMAND_LINE_OPTION)
    )
