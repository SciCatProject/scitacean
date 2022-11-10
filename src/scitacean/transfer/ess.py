# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from contextlib import contextmanager
from getpass import getpass
import os
from pathlib import Path
from typing import Union, Tuple, Optional

# These are quite heavy dependencies.
# It would be great if we could do without them in the long run.
# Note that invoke and paramiko are dependencies of fabric.
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from paramiko.ssh_exception import AuthenticationException, PasswordRequiredException

from ..logging import get_logger
from ..pid import PID


# TODO process multiple files together
# TODO pass pid in put/revert?
#      downloading does not need a pid, so it should not be required in the constructor/
# TODO cache download (maybe using pooch)
class ESSTestFileTransfer:
    """Transfer files to/from test directory at ESS using SSH."""

    def __init__(
        self,
        *,
        host: str = "login.esss.dk",
        port: Optional[int] = None,
        remote_base_path: str = "/mnt/groupdata/scicat/upload",
    ):
        self._host = host
        self._port = port
        self._remote_base_path = remote_base_path

    @contextmanager
    def connect_for_download(self):
        with _connect(self._host, self._port) as con:
            yield _ESSDownloadConnection(connection=con)

    @contextmanager
    def connect_for_upload(self, dataset_id: PID):
        with _connect(self._host, self._port) as con:
            yield _ESSUploadConnection(
                connection=con,
                dataset_id=dataset_id,
                remote_base_path=self._remote_base_path,
            )


class _ESSDownloadConnection:
    def __init__(self, *, connection: Connection):
        self._connection = connection

    def download_file(self, *, remote: Union[str, Path], local: Union[str, Path]):
        """Download a file from the given remote path."""
        get_logger().info(
            "Downloading file %s from host %s to %s",
            remote,
            self._connection.host,
            local,
        )
        self._connection.get(remote=str(remote), local=str(local))


class _ESSUploadConnection:
    def __init__(
        self, *, connection: Connection, dataset_id: PID, remote_base_path: str
    ):
        self._connection = connection
        self._dataset_id = dataset_id
        self._remote_base_path = remote_base_path

    @property
    def source_dir(self) -> str:
        return os.path.join(self._remote_base_path, self._dataset_id.pid)

    def remote_path(self, filename) -> str:
        return os.path.join(self.source_dir, filename)

    def upload_file(self, *, remote: Union[str, Path], local: Union[str, Path]) -> str:
        """Upload a file to the remote staging folder."""
        remote_path = self.remote_path(remote)
        get_logger().info(
            "Uploading file %s to %s on host %s", local, remote, self._connection.host
        )

        self._connection.run(f"mkdir -p {self.source_dir}", hide=True)
        try:
            self._connection.put(
                remote=str(remote_path),
                local=str(local),
            )
        except Exception as exc:
            if _folder_is_empty(self._connection, self.source_dir):
                self._connection.run(f"rm -r {self.source_dir}", hide=True)
            raise exc
        return remote_path

    def revert_upload(self, *, remote: Union[str, Path], local: Union[str, Path] = ""):
        """Remove an uploaded file from the remote staging folder."""
        remote_path = self.remote_path(remote)
        get_logger().info(
            "Reverting upload of file %s to %s on host %s",
            local,
            remote_path,
            self._connection.host,
        )

        try:
            self._connection.run(f"rm {remote_path}", hide=True)
        except UnexpectedExit as exc:
            get_logger().warning(
                "Error reverting file %s:\n%s", remote_path, exc.result
            )
            return

        if _folder_is_empty(self._connection, self.source_dir):
            try:
                get_logger().info(
                    "Removing empty remote directory %s on host %s",
                    self.source_dir,
                    self._connection.host,
                )
                self._connection.run(f"rm -r {self.source_dir}", hide=True)
            except UnexpectedExit as exc:
                get_logger().warning(
                    "Failed to remove empty remote directory %s on host:\n%s",
                    self.source_dir,
                    self._connection.host,
                    exc.result,
                )


def _ask_for_key_passphrase() -> str:
    return getpass("The private key is encrypted, enter passphrase: ")


def _ask_for_credentials(host) -> Tuple[str, str]:
    print(f"You need to authenticate to access {host}")
    username = input("Username: ")
    password = getpass("Password: ")
    return username, password


@contextmanager
def _generic_connect(host, port, **kwargs):
    with Connection(host=host, port=port, **kwargs) as con:
        con.open()
        yield con


@contextmanager
def _unauthenticated_connect(host, port):
    with _generic_connect(host, port) as con:
        yield con


@contextmanager
def _authenticated_connect(host, port, exc: AuthenticationException):
    # TODO fail fast if output going to file
    if isinstance(exc, PasswordRequiredException) and "encrypted" in exc.args[0]:
        # TODO does not work anymore, exception is always AuthenticationException
        with _generic_connect(
            host=host,
            port=port,
            connect_kwargs={"passphrase": _ask_for_key_passphrase()},
        ) as con:
            yield con
    else:
        username, password = _ask_for_credentials(host)
        with _generic_connect(
            host=host, port=port, user=username, connect_kwargs={"password": password}
        ) as con:
            yield con


@contextmanager
def _connect(host, port):
    # Catch all exceptions and remove traceback up to this point.
    # We pass secrets as arguments to functions called in this block and those
    # can be leaked through exception handlers.
    try:
        try:
            with _unauthenticated_connect(host, port) as con:
                yield con
        except AuthenticationException as exc:
            with _authenticated_connect(host, port, exc) as con:
                yield con
    except Exception as exc:
        # TODO dedicated exception type?
        raise type(exc)(exc.args) from None
    except BaseException as exc:
        raise type(exc)(exc.args) from None


def _remote_path_exists(con: Connection, path: str) -> bool:
    return con.run(f"stat {path}", hide=True, warn=True).exited == 0


def _folder_is_empty(con, path) -> bool:
    try:
        return con.run(f"ls {path}", hide=True).stdout == ""
    except UnexpectedExit:
        return False  # no further processing is needed in this case
