# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

import os
from contextlib import contextmanager
from getpass import getpass
from pathlib import Path
from typing import List, Optional, Tuple, Union

# These are quite heavy dependencies.
# It would be great if we could do without them in the long run.
# Note that invoke and paramiko are dependencies of fabric.
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from paramiko import SFTPClient
from paramiko.ssh_exception import AuthenticationException, PasswordRequiredException

from ..error import FileUploadError
from ..file import File
from ..logging import get_logger
from ..pid import PID


# TODO implement new multi-file functions
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
        con = _connect(self._host, self._port)
        try:
            yield _ESSDownloadConnection(connection=con)
        finally:
            con.close()

    @contextmanager
    def connect_for_upload(self, dataset_id: PID):
        con = _connect(self._host, self._port)
        try:
            yield _ESSUploadConnection(
                connection=con,
                dataset_id=dataset_id,
                remote_base_path=self._remote_base_path,
            )
        finally:
            con.close()


class _ESSDownloadConnection:
    def __init__(self, *, connection: Connection):
        self._connection = connection

    def download_files(self, *, remote: List[str], local: List[Path]):
        """Download files from the given remote path."""
        for (r, l) in zip(remote, local):
            self.download_file(remote=r, local=l)

    def download_file(self, *, remote: str, local: Path):
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
    def _sftp(self) -> SFTPClient:
        return self._connection.sftp()

    @property
    def source_dir(self) -> str:
        return os.path.join(self._remote_base_path, self._dataset_id.pid)

    def remote_path(self, filename) -> str:
        return os.path.join(self.source_dir, filename)

    def _make_source_folder(self):
        try:
            self._sftp.mkdir(self.source_dir)
        except OSError as exc:
            raise FileUploadError(
                f"Failed to create source folder: {exc.args}"
            ) from None

    def upload_files(self, *files: File) -> List[File]:
        """Upload files to the remote folder."""
        # TODO revert if any fails
        self._make_source_folder()
        return [self._upload_file(file) for file in files]

        # except Exception as exc:
        #     if _folder_is_empty(self._connection, self.source_dir):
        #         self._connection.run(f"rm -r {self.source_dir}", hide=True)
        #     raise exc

    def _upload_file(self, file: File) -> File:
        remote_path = self.remote_path(file.remote_path)
        get_logger().info(
            "Uploading file %s to %s on host %s",
            file.local_path,
            remote_path,
            self._connection.host,
        )
        self._sftp.put(remotepath=remote_path, localpath=str(file.local_path))
        st = self._sftp.stat(remote_path)
        return file.uploaded(
            remote_gid=st.st_gid,
            remote_uid=st.st_uid,
            remote_creation_time=st.st_mtime,
            remote_perm=st.st_mode,
        )

    def revert_upload(self, *files: File):
        """Remove uploaded files from the remote folder."""
        for file in files:
            self._revert_upload_single(remote=file.remote_path, local=file.local_path)

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

    def _revert_upload_single(
        self, *, remote: Union[str, Path], local: Union[str, Path] = ""
    ):
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


def _ask_for_key_passphrase() -> str:
    return getpass("The private key is encrypted, enter passphrase: ")


def _ask_for_credentials(host: str) -> Tuple[str, str]:
    print(f"You need to authenticate to access {host}")
    username = input("Username: ")
    password = getpass("Password: ")
    return username, password


def _generic_connect(host: str, port: Optional[int], **kwargs) -> Connection:
    con = Connection(host=host, port=port, **kwargs)
    con.open()
    return con


def _unauthenticated_connect(host: str, port: Optional[int]) -> Connection:
    return _generic_connect(host=host, port=port)


def _authenticated_connect(
    host: str, port: Optional[int], exc: AuthenticationException
) -> Connection:
    # TODO fail fast if output going to file
    if isinstance(exc, PasswordRequiredException) and "encrypted" in exc.args[0]:
        # TODO does not work anymore, exception is always AuthenticationException
        return _generic_connect(
            host=host,
            port=port,
            connect_kwargs={"passphrase": _ask_for_key_passphrase()},
        )
    else:
        username, password = _ask_for_credentials(host)
        return _generic_connect(
            host=host, port=port, user=username, connect_kwargs={"password": password}
        )


def _connect(host: str, port: Optional[int]) -> Connection:
    # Catch all exceptions and remove traceback up to this point.
    # We pass secrets as arguments to functions called in this block and those
    # can be leaked through exception handlers.
    try:
        try:
            return _unauthenticated_connect(host, port)
        except AuthenticationException as exc:
            return _authenticated_connect(host, port, exc)
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
