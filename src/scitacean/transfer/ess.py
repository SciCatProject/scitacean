# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from contextlib import contextmanager
from getpass import getpass
import logging
import os
from pathlib import Path
from typing import Union, Tuple, Optional

# These are quite heavy dependencies.
# It would be great if we could do without them in the long run.
# Note that invoke and paramiko are dependencies of fabric.
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from paramiko.ssh_exception import AuthenticationException, PasswordRequiredException


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
        remote_base_path: str = "/mnt/groupdata/scicat/upload",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self._host = host
        self._remote_base_path = remote_base_path
        # TODO really store them?
        self._username = username
        self._password = password

    @staticmethod
    def _ask_for_key_passphrase() -> str:
        return getpass("The private key is encrypted, enter passphrase: ")

    def _ask_for_credentials(self) -> Tuple[str, str]:
        print(f"You need to authenticate to access {self._host}")
        username = input("Username: ")
        password = getpass("Password: ")
        return username, password

    @contextmanager
    def _generic_connect(self, **kwargs):
        with Connection(self._host, **kwargs) as con:
            con.open()
            yield con

    @contextmanager
    def _unauthenticated_connect(self):
        with self._generic_connect() as con:
            yield con

    @contextmanager
    def _authenticated_connect(self, exc: AuthenticationException):
        # TODO fail fast if output going to file
        if isinstance(exc, PasswordRequiredException) and "encrypted" in exc.args[0]:
            with self._generic_connect(
                connect_kwargs={
                    "passphrase": ESSTestFileTransfer._ask_for_key_passphrase()
                }
            ) as con:
                yield con
        else:
            if self._username is not None and self._password is not None:
                username, password = self._username, self._password
            else:
                username, password = self._ask_for_credentials()
            with self._generic_connect(
                user=username, connect_kwargs={"password": password}
            ) as con:
                yield con

    @contextmanager
    def _connect(self):
        try:
            with self._unauthenticated_connect() as con:
                yield con
        except AuthenticationException as exc:
            # TODO backtrace is confusing when the op fails
            #  because it includes the previous exception
            with self._authenticated_connect(exc) as con:
                yield con

    @contextmanager
    def connect_for_download(self):
        with self._connect() as con:
            yield _ESSDownloadConnection(connection=con)

    @contextmanager
    def connect_for_upload(self, dataset_id):
        with self._connect() as con:
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
        _get_logger().info(
            "Downloading file %s from host %s to %s",
            remote,
            self._connection.host,
            local,
        )
        self._connection.get(remote=str(remote), local=str(local))


class _ESSUploadConnection:
    def __init__(
        self, *, connection: Connection, dataset_id: str, remote_base_path: str
    ):
        self._connection = connection
        self._dataset_id = dataset_id
        self._remote_base_path = remote_base_path

    @property
    def source_dir(self) -> str:
        return os.path.join(self._remote_base_path, self._dataset_id)

    def remote_path(self, filename) -> str:
        return os.path.join(self.source_dir, filename)

    def upload_file(self, *, remote: Union[str, Path], local: Union[str, Path]) -> str:
        """Upload a file to the remote staging folder."""
        remote_path = self.remote_path(remote)
        _get_logger().info(
            "Uploading file %s to %s on host %s", local, remote, self._connection.host
        )

        self._connection.run(f"mkdir -p {self.source_dir}", hide=True)
        self._connection.put(
            remote=str(remote_path),
            local=str(local),
        )
        return remote_path

    def revert_upload(self, *, remote: Union[str, Path], local: Union[str, Path] = ""):
        """Remove an uploaded file from the remote staging folder."""
        remote_path = self.remote_path(remote)
        _get_logger().info(
            "Reverting upload of file %s to %s on host %s",
            local,
            remote_path,
            self._connection.host,
        )

        def _folder_is_empty(con, path) -> bool:
            try:
                return con.run(f"ls {path}", hide=True).stdout == ""
            except UnexpectedExit:
                return False  # no further processing is needed in this case

        try:
            self._connection.run(f"rm {remote_path}", hide=True)
        except UnexpectedExit as exc:
            _get_logger().warning(
                "Error reverting file %s:\n%s", remote_path, exc.result
            )
            return

        if _folder_is_empty(self._connection, self.source_dir):
            try:
                _get_logger().info(
                    "Removing empty remote directory %s on host %s",
                    self.source_dir,
                    self._connection.host,
                )
                self._connection.run(f"rm -r {self.source_dir}", hide=True)
            except UnexpectedExit as exc:
                _get_logger().warning(
                    "Failed to remove empty remote directory %s on host:\n%s",
                    self.source_dir,
                    self._connection.host,
                    exc.result,
                )


def _get_logger():
    return logging.getLogger("ESSTestFileTransfer")


def _remote_path_exists(con: Connection, path: str) -> bool:
    return con.run(f"stat {path}", hide=True, warn=True).exited == 0
