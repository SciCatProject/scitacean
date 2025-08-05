# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""File transfer that copies files between locations on the same filesystem."""

import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from ..dataset import Dataset
from ..error import FileNotAccessibleError, FileUploadError
from ..file import File
from ..filesystem import RemotePath
from ..logging import get_logger
from ._util import source_folder_for


class CopyDownloadConnection:
    """Connection for 'downloading' files by copying them.

    Should be created using
    :meth:`scitacean.transfer.copy.CopyFileTransfer.connect_for_download`.
    """

    def __init__(self, hard_link: bool) -> None:
        self._hard_link = hard_link

    def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
        """Download files from the given remote path."""
        for r, l in zip(remote, local, strict=True):
            self.download_file(remote=r, local=l)

    def download_file(self, *, remote: RemotePath, local: Path) -> None:
        """Download a file from the given remote path."""
        get_logger().info(
            "Copying file %s to %s",
            remote,
            local,
        )
        remote_path = Path(remote.posix)
        if not remote_path.exists():
            raise FileNotAccessibleError(
                f"Unable to copy to remote file {remote_path}: File does not exist. "
                "This might mean that your machine does not have direct filesystem "
                "access to the file server. Consider using a different file transfer.",
                remote_path=remote,
            )
        if self._hard_link:
            os.link(src=remote_path, dst=local)
        else:
            shutil.copy(src=remote_path, dst=local)


class CopyUploadConnection:
    """Connection for 'uploading' files by copying.

    Should be created using
    :meth:`scitacean.transfer.copy.CopyFileTransfer.connect_for_upload`.
    """

    def __init__(self, *, source_folder: RemotePath, hard_link: bool) -> None:
        self._source_folder = source_folder
        self._hard_link = hard_link

    @property
    def source_folder(self) -> RemotePath:
        """The source folder this connection uploads to."""
        return self._source_folder

    def remote_path(self, filename: str | RemotePath) -> RemotePath:
        """Return the complete remote path for a given path."""
        return self.source_folder / filename

    def _make_source_folder(self) -> None:
        try:
            Path(self.source_folder.posix).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise FileUploadError(
                f"Failed to create source folder {self.source_folder}: {exc.args}"
            ) from None

    def upload_files(self, *files: File) -> list[File]:
        """Upload files to the remote folder."""
        self._make_source_folder()
        uploaded: list[File] = []
        try:
            uploaded.extend(self._upload_file(file) for file in files)
        except Exception:
            self.revert_upload(*uploaded)
            raise
        return uploaded

    def _upload_file(self, file: File) -> File:
        if file.local_path is None:
            raise ValueError(
                f"Cannot upload file to {file.remote_path}, the file has no local path"
            )
        remote_path = self.remote_path(file.remote_path)
        if Path(remote_path.posix).exists():
            raise FileExistsError(
                f"Refusing to upload file{file.local_path}: "
                f"File already exists at {remote_path}."
            )

        get_logger().info(
            "Copying file %s to %s",
            file.local_path,
            remote_path,
        )
        if self._hard_link:
            os.link(src=file.local_path, dst=remote_path.posix)
        else:
            shutil.copy(src=file.local_path, dst=remote_path.posix)
        st = file.local_path.stat()
        return file.uploaded(
            remote_gid=str(st.st_gid),
            remote_uid=str(st.st_uid),
            remote_creation_time=datetime.now().astimezone(timezone.utc),
            remote_perm=str(st.st_mode),
            remote_size=st.st_size,
        )

    def revert_upload(self, *files: File) -> None:
        """Remove uploaded files from the remote folder."""
        for file in files:
            self._revert_upload_single(remote=file.remote_path, local=file.local_path)

        if _remote_folder_is_empty(self.source_folder):
            try:
                get_logger().info(
                    "Removing empty remote directory %s",
                    self.source_folder,
                )
                Path(self.source_folder.posix).rmdir()
            except OSError as exc:
                get_logger().warning(
                    "Failed to remove empty remote directory %s:\n%s",
                    self.source_folder,
                    exc,
                )

    def _revert_upload_single(self, *, remote: RemotePath, local: Path | None) -> None:
        remote_path = self.remote_path(remote)
        get_logger().info(
            "Reverting upload of file %s to %s",
            local,
            remote_path,
        )

        try:
            Path(remote_path.posix).unlink(missing_ok=True)
        except OSError as exc:
            get_logger().warning("Error reverting file %s:\n%s", remote_path, exc)
            return


class CopyFileTransfer:
    """Upload / download files by copying files on the same filesystem.

    This file transfer requires that the 'remote' file system is directly
    accessible from the 'local' file system.
    It copies the 'remote' files directly to the local download folder.

    Note
    ----
    A note on terminology:
    In Scitacean, 'remote' refers to the file server where the data files
    are stored that belong to SciCat datasets.
    In contrast, 'local' refers to the file system of the machine that
    runs the Python process.
    The two filesystems can be the same.
    However, Scitacean maintains a strict separation between the two and
    uses 'downloaders' and 'uploaders' to transfer between them even if that
    transfer is a simple copy.

    See also the documentation of :class:`scitacean.File`.

    Warning
    -------
    This file transfer does not work on Windows because it converts between
    :class:`RemotePath` and :class:`pathlib.Path`.
    This requires that both use the same directory separators.
    Since :class:`RemotePath` uses UNIX-style forward slashes, it is
    incompatible with Windows paths.
    In practice, this should not be a problem because SciCat file storage
    should never be a Windows server.

    Examples
    --------
    Given a dataset with ``source_folder="/dataset/source"`` and a file with path
    ``"file1.dat"``, this

    .. code-block:: python

        client = Client.from_token(
            url="...",
            token="...",
            file_transfer=CopyFileTransfer()
        )
        ds = client.get_dataset(pid="...")
        ds = client.download_files(ds, target="/downloads")

    copies the file from ``/dataset/source/file1.dat`` to ``/downloads/file1.dat``.
    """

    def __init__(
        self,
        *,
        source_folder: str | RemotePath | None = None,
        hard_link: bool = False,
    ) -> None:
        """Construct a new Copy file transfer.

        Warning
        -------
        When using hard links (with ``hard_link = True``), the downloaded
        or uploaded files will refer to the same bytes.
        So if one is modified, the other will be modified as well.
        Use this feature with care!

        Parameters
        ----------
        source_folder:
            Upload files to this folder if set.
            Otherwise, upload to the dataset's source_folder.
            Ignored when downloading files.
        hard_link:
            If True, try to use hard links instead of copies.
        """
        self._source_folder_pattern = (
            RemotePath(source_folder) if source_folder is not None else None
        )
        self._hard_link = hard_link

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        """Return the source folder used for the given dataset."""
        return source_folder_for(dataset, self._source_folder_pattern)

    @contextmanager
    def connect_for_download(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[CopyDownloadConnection]:
        """Create a connection for downloads, use as a context manager.

        Parameters
        ----------
        dataset:
            The dataset for which to download files.
        representative_file_path:
            A path to a file that can be used to check whether files for this
            dataset are accessible.
            The transfer assumes that, if this path is accessible,
            all files for this dataset are.

        Returns
        -------
        :
            A connection object that can download files.

        Raises
        ------
        FileNotAccessibleError
            If files for the given dataset cannot be accessed
            based on ``representative_file_path``.
        """
        source_folder = self.source_folder_for(dataset)
        if not Path(source_folder.posix).exists():
            raise FileNotAccessibleError(
                "Cannot directly access the source folder",
                remote_path=source_folder,
            )
        if not Path((source_folder / representative_file_path).posix).exists():
            raise FileNotAccessibleError(
                "Cannot directly access the file", remote_path=representative_file_path
            )
        yield CopyDownloadConnection(self._hard_link)

    @contextmanager
    def connect_for_upload(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[CopyUploadConnection]:
        """Create a connection for uploads, use as a context manager.

        Parameters
        ----------
        dataset:
            The connection will be used to upload files of this dataset.
            Used to determine the target folder.
        representative_file_path:
            A path on the remote to check whether files for this
            dataset can be written.
            The transfer assumes that, if it is possible to write to this path,
            it is possible to write to the paths of all files to be uploaded.

        Returns
        -------
        :
            An open :class:`CopyUploadConnection` object.

        Raises
        ------
        FileNotAccessibleError
            If the remote folder cannot be accessed
            based on ``representative_file_path``.
        """
        source_folder = Path(self.source_folder_for(dataset).posix)
        if not source_folder.parents[-2].exists():
            # This check may have a lot of false negatives.
            # But we cannot check whether `source_folder` exists because the user
            # may intend for the upload to create that folder.
            # Checking the top level parent after the root should still catch many
            # cases as long as the remote uses paths are uncommon on user machines.
            # E.g., for /ess/data/2025/... we get parents[-2] = /ess which should
            # not exist on non-ess machines.
            raise FileNotAccessibleError(
                "Cannot directly access the source folder",
                remote_path=self.source_folder_for(dataset),
            )
        yield CopyUploadConnection(
            source_folder=self.source_folder_for(dataset), hard_link=self._hard_link
        )


def _remote_folder_is_empty(path: RemotePath) -> bool:
    try:
        _ = next(iter(Path(path.posix).iterdir()))
    except StopIteration:
        return True
    return False


__all__ = ["CopyDownloadConnection", "CopyFileTransfer", "CopyUploadConnection"]
