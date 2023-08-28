# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Tuple, Union

from invoke.exceptions import UnexpectedExit
from paramiko import SFTPAttributes, SFTPClient, SSHClient

from ..dataset import Dataset
from ..error import FileUploadError
from ..file import File
from ..filesystem import RemotePath
from ..logging import get_logger
from .util import source_folder_for


class SFTPDownloadConnection:
    def __init__(self, *, sftp_client: SFTPClient, host: str) -> None:
        self._sftp_client = sftp_client
        self._host = host

    def download_files(self, *, remote: List[RemotePath], local: List[Path]) -> None:
        """Download files from the given remote path."""
        for r, l in zip(remote, local):
            self.download_file(remote=r, local=l)

    def download_file(self, *, remote: RemotePath, local: Path) -> None:
        get_logger().info(
            "Downloading file %s from host %s to %s",
            remote,
            self._host,
            local,
        )
        self._sftp_client.get(remotepath=remote.posix, localpath=os.fspath(local))


class SFTPUploadConnection:
    def __init__(
        self, *, sftp_client: SFTPClient, source_folder: RemotePath, host: str
    ) -> None:
        self._sftp_client = sftp_client
        self._source_folder = source_folder
        self._host = host

    @property
    def source_folder(self) -> RemotePath:
        return self._source_folder

    def remote_path(self, filename: Union[str, RemotePath]) -> RemotePath:
        return self.source_folder / filename

    def _make_source_folder(self) -> None:
        try:
            _mkdir_remote(self._sftp_client, self.source_folder)
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
        if file.local_path is None:
            raise ValueError(
                f"Cannot upload file to {file.remote_path}, "
                "the file has no local path"
            )
        remote_path = self.remote_path(file.remote_path)
        get_logger().info(
            "Uploading file %s to %s on host %s",
            file.local_path,
            remote_path,
            self._host,
        )
        st = self._sftp_client.put(
            remotepath=remote_path.posix, localpath=os.fspath(file.local_path)
        )
        if (exc := self._validate_upload(file)) is not None:
            return file, exc
        return (
            file.uploaded(
                remote_gid=str(st.st_gid),
                remote_uid=str(st.st_uid),
                remote_creation_time=datetime.now().astimezone(timezone.utc),
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
        return None

    def _compute_checksum(self, file: File) -> Optional[str]:
        if file.checksum_algorithm is None:
            return None
        return _compute_remote_checksum(
            self._sftp_client,
            self.remote_path(file.remote_path),
            file.checksum_algorithm,
        )

    def revert_upload(self, *files: File) -> None:
        """Remove uploaded files from the remote folder."""
        for file in files:
            self._revert_upload_single(remote=file.remote_path, local=file.local_path)

        if _remote_folder_is_empty(self._sftp_client, self.source_folder):
            try:
                get_logger().info(
                    "Removing empty remote directory %s on host %s",
                    self.source_folder,
                    self._host,
                )
                self._sftp_client.rmdir(self.source_folder.posix)
            except UnexpectedExit as exc:
                get_logger().warning(
                    "Failed to remove empty remote directory %s on host:\n%s",
                    self.source_folder,
                    self._host,
                    exc.result,
                )

    def _revert_upload_single(
        self, *, remote: RemotePath, local: Optional[Path]
    ) -> None:
        remote_path = self.remote_path(remote)
        get_logger().info(
            "Reverting upload of file %s to %s on host %s",
            local,
            remote_path,
            self._host,
        )

        try:
            self._sftp_client.remove(remote_path.posix)
        except UnexpectedExit as exc:
            get_logger().warning(
                "Error reverting file %s:\n%s", remote_path, exc.result
            )
            return


class SFTPFileTransfer:
    """Upload / download files using SFTP.

    Configuration & Authentication
    ------------------------------
    The file transfer connects to the server at the address given
    as the ``host`` constructor argument.
    This may be

    - a full url such as ``some.fileserver.edu``,
    - an IP address like ``127.0.0.1``,
    - or a host defined in the user's openSFTP config file.

    The file transfer can authenticate using username+password.
    It will ask for those on the command line.
    However, it is **highly recommended to set up a key and use an SFTP agent!**
    This increases security as Scitacean no longer has to handle credentials itself.
    And it is required for automated programs where a user cannot enter credentials
    on a command line.

    Upload folder
    -------------
    The file transfer can take an optional ``source_folder`` as a constructor argument.
    If it is given, ``SFTPFileTransfer`` uploads all files to it and ignores the
    source folder set in the dataset.
    If it is not given, ``SFTPFileTransfer`` uses the dataset's source folder.

    The source folder argument to ``SFTPFileTransfer`` may be a Python format string.
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

        file_transfer = SFTPFileTransfer(host="fileserver")

    This uploads to ``/transfer/folder``:

    .. code-block:: python

        file_transfer = SFTPFileTransfer(host="fileserver",
                                        source_folder="transfer/folder")

    This uploads to ``/transfer/my-dataset``:
    (Note that ``{name}`` is replaced by ``dset.name``.)

    .. code-block:: python

        file_transfer = SFTPFileTransfer(host="fileserver",
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
        source_folder: Optional[Union[str, RemotePath]] = None,
        connect: Optional[Callable[[str, Optional[int]], SFTPClient]] = None,
    ) -> None:
        """Construct a new SFTP file transfer.

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
        connect:
            If this argument is set, it will be called to create a client
            for the server instead of the builtin method.
            The function arguments are ``host`` and ``port`` as determined by the
            arguments to ``__init__`` shown above.
        """
        self._host = host
        self._port = port
        self._source_folder_pattern = (
            RemotePath(source_folder)
            if isinstance(source_folder, str)
            else source_folder
        )
        self._connect = connect

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        """Return the source folder used for the given dataset."""
        return source_folder_for(dataset, self._source_folder_pattern)

    @contextmanager
    def connect_for_download(self) -> Iterator[SFTPDownloadConnection]:
        """Create a connection for downloads, use as a context manager."""
        sftp_client = _connect(self._host, self._port, connect=self._connect)
        try:
            yield SFTPDownloadConnection(sftp_client=sftp_client, host=self._host)
        finally:
            sftp_client.close()

    @contextmanager
    def connect_for_upload(self, dataset: Dataset) -> Iterator[SFTPUploadConnection]:
        """Create a connection for uploads, use as a context manager.

        Parameters
        ----------
        dataset:
            The connection will be used to upload files of this dataset.
            Used to determine the target folder.
        """
        source_folder = self.source_folder_for(dataset)
        sftp_client = _connect(self._host, self._port, connect=self._connect)
        try:
            yield SFTPUploadConnection(
                sftp_client=sftp_client, source_folder=source_folder, host=self._host
            )
        finally:
            sftp_client.close()


def _default_connect(host: str, port: Optional[int]) -> SFTPClient:
    client = SSHClient()
    client.load_system_host_keys()
    if port is not None:
        client.connect(hostname=host, port=port)
    else:
        client.connect(hostname=host)
    return client.open_sftp()


def _connect(
    host: str,
    port: Optional[int],
    connect: Optional[Callable[[str, Optional[int]], SFTPClient]],
) -> SFTPClient:
    try:
        if connect is None:
            connect = _default_connect
        return connect(host, port)
    except Exception as exc:
        # We pass secrets as arguments to functions called in this block, and those
        # can be leaked through exception handlers. So catch all exceptions
        # and strip the backtrace up to this point to hide those secrets.
        raise type(exc)(exc.args) from None


def _remote_folder_is_empty(sftp: SFTPClient, path: RemotePath) -> bool:
    return not sftp.listdir(path.posix)


def _mkdir_remote(sftp: SFTPClient, path: RemotePath) -> None:
    if (parent := path.parent) not in (".", "/"):
        _mkdir_remote(sftp, parent)

    st_stat = _try_remote_stat(sftp, path)
    if st_stat is None:
        sftp.mkdir(path.posix)
    elif not _is_remote_dir(st_stat):
        raise FileExistsError(
            f"Cannot make directory because path points to a file: {path}"
        )


def _try_remote_stat(sftp: SFTPClient, path: RemotePath) -> Optional[SFTPAttributes]:
    try:
        return sftp.stat(path.posix)
    except FileNotFoundError:
        return None


def _is_remote_dir(st_stat: SFTPAttributes) -> bool:
    if st_stat.st_mode is None:
        return True  # Assume it is a dir and let downstream code fail if it isn't.
    return st_stat.st_mode & 0o040000 == 0o040000


def _compute_remote_checksum(
    sftp: SFTPClient, path: RemotePath, checksum_algorithm: str
) -> Optional[str]:
    with sftp.open(path.posix, "r") as f:
        try:
            return f.check(checksum_algorithm).decode("utf-8")
        except OSError as exc:
            # Many servers don't support this.
            # See https://docs.paramiko.org/en/latest/api/sftp.html
            if "Operation unsupported" in exc.args:
                return None
            raise


__all__ = ["SFTPFileTransfer", "SFTPUploadConnection", "SFTPDownloadConnection"]
