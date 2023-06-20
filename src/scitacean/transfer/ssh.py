# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from getpass import getpass
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional, Tuple, Union

from dateutil.tz import tzoffset

# Note that invoke and paramiko are dependencies of fabric.
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from paramiko import SFTPClient
from paramiko.ssh_exception import AuthenticationException, PasswordRequiredException

from ..dataset import Dataset
from ..error import FileUploadError
from ..file import File
from ..filesystem import RemotePath
from ..logging import get_logger
from .util import source_folder_for

# TODO pass pid in put/revert?
#      downloading does not need a pid, so it should not be required in the constructor/


class SSHDownloadConnection:
    def __init__(self, *, connection: Connection) -> None:
        self._connection = connection

    def download_files(self, *, remote: List[RemotePath], local: List[Path]) -> None:
        """Download files from the given remote path."""
        for r, l in zip(remote, local):
            self.download_file(remote=r, local=l)

    def download_file(self, *, remote: RemotePath, local: Path) -> None:
        get_logger().info(
            "Downloading file %s from host %s to %s",
            remote,
            self._connection.host,
            local,
        )
        self._connection.get(remote=remote.posix, local=os.fspath(local))


class SSHUploadConnection:
    def __init__(self, *, connection: Connection, source_folder: RemotePath) -> None:
        self._connection = connection
        self._source_folder = source_folder
        self._remote_timezone = self._get_remote_timezone()

    @property
    def _sftp(self) -> SFTPClient:
        return self._connection.sftp()  # type: ignore[no-any-return]

    @property
    def source_folder(self) -> RemotePath:
        return self._source_folder

    def remote_path(self, filename: Union[str, RemotePath]) -> RemotePath:
        return self.source_folder / filename

    def _make_source_folder(self) -> None:
        try:
            self._connection.run(
                f"mkdir -p {self.source_folder.posix}", hide=True, in_stream=False
            )
        except OSError as exc:
            raise FileUploadError(
                f"Failed to create source folder {self.source_folder}: {exc.args}"
            ) from None

    def upload_files(self, *files: File) -> List[File]:
        """Upload files to the remote folder."""
        self._make_source_folder()
        uploaded = []
        try:
            for file in files:
                up, exc = self._upload_file(file)
                uploaded.append(up)  # need to add this file in order to revert it
                if exc is not None:
                    raise exc
        except Exception:
            self.revert_upload(*uploaded)
            raise
        return uploaded

    def _upload_file(self, file: File) -> Tuple[File, Optional[Exception]]:
        remote_path = self.remote_path(file.remote_path)
        get_logger().info(
            "Uploading file %s to %s on host %s",
            file.local_path,
            remote_path,
            self._connection.host,
        )
        st = self._sftp.put(
            remotepath=remote_path.posix, localpath=os.fspath(file.local_path)
        )
        if (exc := self._validate_upload(file)) is not None:
            return file, exc
        creation_time = (
            datetime.fromtimestamp(st.st_mtime, tz=self._remote_timezone)
            if st.st_mtime
            else None
        )
        return (
            file.uploaded(
                remote_gid=str(st.st_gid),
                remote_uid=str(st.st_uid),
                remote_creation_time=creation_time,
                remote_perm=str(st.st_mode),
                remote_size=st.st_size,
            ),
            None,
        )

    def _validate_upload(self, file: File) -> Optional[Exception]:
        if (checksum := self._compute_checksum(file)) is None:
            return None
        if checksum != file.checksum():
            return FileUploadError(
                f"Upload of file {file.remote_path} failed: "
                f"Checksum of uploaded file ({checksum}) does not "
                f"match checksum of local file ({file.checksum()}) "
                f"using algorithm {file.checksum_algorithm}"
            )

    def _compute_checksum(self, file: File) -> Optional[str]:
        if (hash_exe := _coreutils_checksum_for(file)) is None:
            return None
        try:
            res = self._connection.run(
                f"{hash_exe} {self.remote_path(file.remote_path).posix}",
                hide=True,
                in_stream=False,
            )
        except UnexpectedExit as exc:
            if exc.result.return_code == 127:
                get_logger().warning(
                    "Cannot validate checksum of uploaded file %s because checksum "
                    "algorithm '%s' is not implemented on the server.",
                    file.remote_path,
                    file.checksum_algorithm,
                )
                return None
            raise
        return res.stdout.split(" ", 1)[0]  # type: ignore[no-any-return]

    def _get_remote_timezone(self) -> tzoffset:
        cmd = 'date +"%Z|%::z"'
        try:
            tz_str = self._connection.run(
                cmd, hide=True, in_stream=False
            ).stdout.strip()
        except UnexpectedExit as exc:
            raise FileUploadError(
                f"Failed to get timezone of fileserver: {exc.args}"
            ) from None
        tz = _parse_remote_timezone(tz_str)
        get_logger().info("Detected timezone of fileserver: %s", tz)
        return tz

    def revert_upload(self, *files: File) -> None:
        """Remove uploaded files from the remote folder."""
        for file in files:
            self._revert_upload_single(
                remote=file.remote_path, local=file.local_path
            )  # type: ignore[arg-type]

        if _folder_is_empty(self._connection, self.source_folder):
            try:
                get_logger().info(
                    "Removing empty remote directory %s on host %s",
                    self.source_folder,
                    self._connection.host,
                )
                self._sftp.rmdir(self.source_folder.posix)
            except UnexpectedExit as exc:
                get_logger().warning(
                    "Failed to remove empty remote directory %s on host:\n%s",
                    self.source_folder,
                    self._connection.host,
                    exc.result,
                )

    def _revert_upload_single(self, *, remote: RemotePath, local: Path) -> None:
        remote_path = self.remote_path(remote)
        get_logger().info(
            "Reverting upload of file %s to %s on host %s",
            local,
            remote_path,
            self._connection.host,
        )

        try:
            self._sftp.remove(remote_path.posix)
        except UnexpectedExit as exc:
            get_logger().warning(
                "Error reverting file %s:\n%s", remote_path, exc.result
            )
            return


class SSHFileTransfer:
    """Upload / download files using SSH.

    Configuration & Authentication
    ------------------------------
    The file transfer connects to the server at the address given
    as the ``host`` constructor argument.
    This may be

    - a full url such as ``some.fileserver.edu``,
    - an IP address like ``127.0.0.1``,
    - or a host defined in the user's openSSH config file.

    The file transfer can authenticate using username+password.
    It will ask for those on the command line.
    However, it is **highly recommended to set up a key and use an SSH agent!**
    This increases security as Scitacean no longer has to handle credentials itself.
    And it is required for automated programs where a user cannot enter credentials
    on a command line.

    Upload folder
    -------------
    The file transfer can take an optional ``source_folder`` as a constructor argument.
    If it is given, ``SSHFileTransfer`` uploads all files to it and ignores the
    source folder set in the dataset.
    If it is not given, ``SSHFileTransfer`` uses the dataset's source folder.

    The source folder argument to ``SSHFileTransfer`` may be a Python format string.
    In that case, all format fields are replaced by the corresponding fields
    of the dataset.
    All non-ASCII characters and most special ASCII characters are replaced.
    This should avoid broken paths from essentially random contents in datasets.

    Examples
    --------
    Given

    .. code-block:: python

        dset = Dataset(type="raw",
                       name="my-dataset",
                       source_folder="/dataset/source",
                       )

    This uploads to ``/dataset/source``:

    .. code-block:: python

        file_transfer = SSHFileTransfer(host="fileserver")

    This uploads to ``/transfer/folder``:

    .. code-block:: python

        file_transfer = SSHFileTransfer(host="fileserver",
                                        source_folder="transfer/folder")

    This uploads to ``/transfer/my-dataset``:
    (Note that ``{name}`` is replaced by ``dset.name``.)

    .. code-block:: python

        file_transfer = SSHFileTransfer(host="fileserver",
                                        source_folder="transfer/{name}")

    A useful approach is to include a unique ID in the source folder, for example
    ``"/some/base/folder/{uid}"``, to avoid clashes between different datasets.
    Scitacean will fill in the ``"{uid}"`` placeholder with a new UUID4.
    """

    def __init__(
        self,
        *,
        host: str,
        port: Optional[int] = None,
        source_folder: Optional[Union[str, Path]] = None,
    ) -> None:
        """Construct a new SSH file transfer.

        Parameters
        ----------
        host:
            URL or name of the server to connect to.
        port:
            Port of the server.
        source_folder:
            Upload files to this folder if set.
            Otherwise, upload to the dataset's source_folder.
            Ignored when downloading files.
        """
        self._host = host
        self._port = port
        self._source_folder_pattern = (
            RemotePath(source_folder)
            if isinstance(source_folder, str)
            else source_folder
        )

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        """Return the source folder used for the given dataset."""
        return source_folder_for(dataset, self._source_folder_pattern)

    @contextmanager
    def connect_for_download(
        self, connect: Optional[Callable[..., Connection]] = None
    ) -> Iterator[SSHDownloadConnection]:
        """Create a connection for downloads, use as a context manager.

        Parameters
        ----------
        connect:
            A function that creates and returns a :class:`fabric.connection.Connection`
            object.
            Will first be called with only ``host`` and ``port``.
            If this fails (by raising
            :class:`paramiko.ssh_exception.AuthenticationException`), the function is
            called with ``host``, ``port``, and, optionally, ``user`` and
            ``connection_kwargs`` depending on the authentication method.
            Raising :class:`paramiko.ssh_exception.AuthenticationException` in the 2nd
            call or any other exception in the 1st signals failure of
            ``connect_for_download``.
        """
        con = _connect(self._host, self._port, connect=connect)
        try:
            yield SSHDownloadConnection(connection=con)
        finally:
            con.close()

    @contextmanager
    def connect_for_upload(
        self, dataset: Dataset, connect: Optional[Callable[..., Connection]] = None
    ) -> Iterator[SSHUploadConnection]:
        """Create a connection for uploads, use as a context manager.

        Parameters
        ----------
        dataset:
            The connection will be used to upload files of this dataset.
            Used to determine the target folder.
        connect:
            A function that creates and returns a :class:`fabric.connection.Connection`
            object.
            Will first be called with only ``host`` and ``port``.
            If this fails (by raising
            :class:`paramiko.ssh_exception.AuthenticationException`), the function is
            called with ``host``, ``port``, and, optionally, ``user`` and
            ``connection_kwargs`` depending on the authentication method.
            Raising :class:`paramiko.ssh_exception.AuthenticationException` in the 2nd
            call or any other exception in the 1st signals failure of
            ``connect_for_upload``.
        """
        source_folder = self.source_folder_for(dataset)
        con = _connect(self._host, self._port, connect=connect)
        try:
            yield SSHUploadConnection(
                connection=con,
                source_folder=source_folder,
            )
        finally:
            con.close()


def _ask_for_key_passphrase() -> str:
    return getpass("The private key is encrypted, enter passphrase: ")


def _ask_for_credentials(host: str) -> Tuple[str, str]:
    print(f"You need to authenticate to access {host}")  # noqa: T201
    username = input("Username: ")
    password = getpass("Password: ")
    return username, password


def _generic_connect(
    host: str,
    port: Optional[int],
    connect: Optional[Callable[..., Connection]],
    **kwargs: Any,
) -> Connection:
    if connect is None:
        con = Connection(host=host, port=port, **kwargs)
    else:
        con = connect(host=host, port=port, **kwargs)
    con.open()
    return con


def _unauthenticated_connect(
    host: str, port: Optional[int], connect: Optional[Callable[..., Connection]]
) -> Connection:
    return _generic_connect(host=host, port=port, connect=connect)


def _authenticated_connect(
    host: str,
    port: Optional[int],
    connect: Optional[Callable[..., Connection]],
    exc: AuthenticationException,
) -> Connection:
    # TODO fail fast if output going to file
    if isinstance(exc, PasswordRequiredException) and "encrypted" in exc.args[0]:
        # TODO does not work anymore, exception is always AuthenticationException
        return _generic_connect(
            host=host,
            port=port,
            connect=connect,
            connect_kwargs={"passphrase": _ask_for_key_passphrase()},
        )
    else:
        username, password = _ask_for_credentials(host)
        return _generic_connect(
            host=host,
            port=port,
            connect=connect,
            user=username,
            connect_kwargs={"password": password},
        )


def _connect(
    host: str, port: Optional[int], connect: Optional[Callable[..., Connection]]
) -> Connection:
    try:
        try:
            return _unauthenticated_connect(host, port, connect)
        except AuthenticationException as exc:
            return _authenticated_connect(host, port, connect, exc)
    except Exception as exc:
        # We pass secrets as arguments to functions called in this block, and those
        # can be leaked through exception handlers. So catch all exceptions
        # and strip the backtrace up to this point to hide those secrets.
        raise type(exc)(exc.args) from None
    except BaseException as exc:
        raise type(exc)(exc.args) from None


def _folder_is_empty(con: Connection, path: RemotePath) -> bool:
    try:
        ls: str = con.run(f"ls {path.posix}", hide=True, in_stream=False).stdout
        return ls == ""
    except UnexpectedExit:
        return False  # no further processing is needed in this case


def _coreutils_checksum_for(file: File) -> Optional[str]:
    # blake2s is not supported because `b2sum -l 256` produces a different digest
    # and I don't know why.
    supported = {
        "md5": "md5sum -b",
        "sha256": "sha256sum -b",
        "sha384": "sha384sum -b",
        "sha512": "sha512sum -b",
        "blake2b": "b2sum -l 512 -b",
    }
    algorithm = file.checksum_algorithm
    if algorithm == "blake2s" or algorithm not in supported:
        get_logger().warning(
            "Cannot validate checksum of uploaded file %s because checksum algorithm "
            "'%s' is not supported by scitacean for remote files.",
            file.remote_path,
            file.checksum_algorithm,
        )
        return None
    return supported[algorithm]


# Using `date +"%Z"` returns a timezone abbreviation like CET or EST.
# dateutil.tz.gettz can parse this abbreviation and return a tzinfo object.
# However, on Windows, it returns `None` if the string refers to the local timezone.
# This is indistinguishable from an unrecognised timezone,
# where gettz also returns `None`.
# To avoid this, use an explicit offset obtained from `date +"%::z"`.
# The timezone name is only used for debugging and not interpreted by
# dateutil or datetime.
def _parse_remote_timezone(tz_str: str) -> tzoffset:
    # tz_str is expected to be of the form
    # <tzname>|<hours>:<minutes>:<seconds>
    # as produced by `date +"%Z|%::z"`
    name, offset = tz_str.split("|")
    hours, minutes, seconds = map(int, offset.split(":"))
    return tzoffset(name, timedelta(hours=hours, minutes=minutes, seconds=seconds))
