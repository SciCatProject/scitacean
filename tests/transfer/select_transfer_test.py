# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
from __future__ import annotations

import dataclasses
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import pytest

from scitacean import Dataset, File, RemotePath
from scitacean.transfer.copy import CopyFileTransfer
from scitacean.transfer.link import LinkFileTransfer
from scitacean.transfer.select import SelectFileTransfer


class SuccessfulTransfer:
    def __init__(self) -> None:
        self.downloaded: list[tuple[RemotePath, Path]] = []
        self.uploaded: list[Path] = []
        self.reverted: list[Path] = []
        self.is_open_for_download = False
        self.is_open_for_upload = False

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        raise RuntimeError("Child transfer must not provide source folder")

    @contextmanager
    def connect_for_download(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[SuccessfulTransfer]:
        self.is_open_for_download = True
        yield self
        self.is_open_for_download = False

    @contextmanager
    def connect_for_upload(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[SuccessfulTransfer]:
        self.is_open_for_upload = True
        yield self
        self.is_open_for_upload = False

    def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
        self.downloaded.extend(zip(remote, local, strict=True))

    def upload_files(self, *files: File) -> list[File]:
        self.uploaded.extend(cast(Path, file.local_path) for file in files)
        return [
            dataclasses.replace(
                file,
                remote_path=RemotePath(file.local_path.as_posix()),  # type: ignore[union-attr]
            )
            for file in files
        ]

    def revert_upload(self, *files: File) -> None:
        self.reverted.extend(cast(Path, file.local_path) for file in files)


class FailingTransfer:
    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        raise RuntimeError("Child transfer must not provide source folder")

    @contextmanager
    def connect_for_download(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[FailingTransfer]:
        raise RuntimeError("This transfer always fails")
        # This is needed to make this function a generator and trigger the exception
        # only when the context manager is entered. Without `yield`, the exception is
        # raised when the function is first called. This does not correspond
        # to how real transfers work.
        yield self  # type: ignore[unreachable]

    @contextmanager
    def connect_for_upload(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[FailingTransfer]:
        raise RuntimeError("This transfer always fails")
        # See comment in connect_for_download.
        yield self  # type: ignore[unreachable]

    def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
        raise NotImplementedError()

    def upload_files(self, *files: File) -> list[File]:
        raise NotImplementedError()

    def revert_upload(self, *files: File) -> None:
        raise NotImplementedError()


class FailingDuringTransfer:
    def __init__(self) -> None:
        self.is_open_for_download = False
        self.is_open_for_upload = False

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        raise RuntimeError("Child transfer must not provide source folder")

    @contextmanager
    def connect_for_download(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[FailingDuringTransfer]:
        self.is_open_for_download = True
        yield self
        self.is_open_for_download = False

    @contextmanager
    def connect_for_upload(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[FailingDuringTransfer]:
        self.is_open_for_upload = True
        yield self
        self.is_open_for_upload = False

    def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
        raise RuntimeError("This should propagate to the user")

    def upload_files(self, *files: File) -> list[File]:
        raise RuntimeError("This should propagate to the user")

    def revert_upload(self, *files: File) -> None:
        raise RuntimeError("This should propagate to the user")


@pytest.fixture
def dataset() -> Dataset:
    return Dataset(type="raw", source_folder=RemotePath("/remote/data"))


def test_select_cannot_init_without_children() -> None:
    with pytest.raises(ValueError, match="child transfer must be provided"):
        SelectFileTransfer([])


def test_select_uses_own_source_folder_override() -> None:
    transfer = SelectFileTransfer([SuccessfulTransfer()], source_folder="override")
    assert transfer.source_folder_for(Dataset(type="raw")) == RemotePath("override")


def test_select_download_uses_single_child_transfer_success(dataset: Dataset) -> None:
    transfer_1 = SuccessfulTransfer()
    transfer = SelectFileTransfer([transfer_1])

    remote = dataset.source_folder / "file"  # type: ignore[operator]
    local = Path("local_file")
    with transfer.connect_for_download(dataset, RemotePath("file")) as con:
        con.download_files(remote=[remote], local=[local])

    assert not transfer_1.is_open_for_download
    assert transfer_1.downloaded == [(remote, local)]
    assert not transfer_1.uploaded
    assert not transfer_1.reverted


def test_select_download_uses_single_child_transfer_failure(dataset: Dataset) -> None:
    transfer_1 = FailingTransfer()
    transfer = SelectFileTransfer([transfer_1])

    with pytest.raises(RuntimeError, match="no suitable file transfer available"):
        with transfer.connect_for_download(dataset, RemotePath("file")):
            ...


def test_select_download_fails_gracefully_with_multiple_failing_children(
    dataset: Dataset,
) -> None:
    transfer_1 = FailingTransfer()
    transfer_2 = FailingTransfer()
    transfer = SelectFileTransfer([transfer_1, transfer_2])

    with pytest.raises(RuntimeError, match="no suitable file transfer available"):
        with transfer.connect_for_download(dataset, RemotePath("file")):
            ...


def test_select_download_fails_if_download_fails_after_connection(
    dataset: Dataset,
) -> None:
    transfer_1 = FailingDuringTransfer()
    transfer = SelectFileTransfer([transfer_1])

    remote = dataset.source_folder / "file"  # type: ignore[operator]
    local = Path("local_file")
    with transfer.connect_for_download(dataset, RemotePath("file")) as con:
        assert transfer_1.is_open_for_download
        with pytest.raises(RuntimeError, match="This should propagate to the user"):
            con.download_files(remote=[remote], local=[local])
    assert not transfer_1.is_open_for_download


def test_select_download_uses_first_child_transfer_success(dataset: Dataset) -> None:
    transfer_1 = SuccessfulTransfer()
    transfer_2 = FailingTransfer()
    transfer = SelectFileTransfer([transfer_1, transfer_2])

    remote = dataset.source_folder / "file"  # type: ignore[operator]
    local = Path("local_file")
    with transfer.connect_for_download(dataset, RemotePath("file")) as con:
        con.download_files(remote=[remote], local=[local])

    assert not transfer_1.is_open_for_download
    assert transfer_1.downloaded == [(remote, local)]
    assert not transfer_1.uploaded
    assert not transfer_1.reverted


def test_select_download_uses_second_child_transfer_success(dataset: Dataset) -> None:
    transfer_1 = FailingTransfer()
    transfer_2 = SuccessfulTransfer()
    transfer = SelectFileTransfer([transfer_1, transfer_2])

    remote = dataset.source_folder / "file"  # type: ignore[operator]
    local = Path("local_file")
    with transfer.connect_for_download(dataset, RemotePath("file")) as con:
        con.download_files(remote=[remote], local=[local])

    assert not transfer_2.is_open_for_download
    assert transfer_2.downloaded == [(remote, local)]
    assert not transfer_2.uploaded
    assert not transfer_2.reverted


def test_select_upload_uses_single_child_transfer_success(dataset: Dataset) -> None:
    transfer_1 = SuccessfulTransfer()
    transfer = SelectFileTransfer([transfer_1])

    file = File.from_local("local_file", remote_path="remote_file")
    with transfer.connect_for_upload(dataset, RemotePath("remote_file")) as con:
        con.upload_files(file)

    assert not transfer_1.is_open_for_upload
    assert transfer_1.uploaded == [file.local_path]
    assert not transfer_1.reverted
    assert not transfer_1.downloaded


def test_select_upload_uses_single_child_transfer_failure(dataset: Dataset) -> None:
    transfer_1 = FailingTransfer()
    transfer = SelectFileTransfer([transfer_1])

    with pytest.raises(RuntimeError, match="no suitable file transfer available"):
        with transfer.connect_for_upload(dataset, RemotePath("file")):
            ...


def test_select_upload_fails_gracefully_with_multiple_failing_children(
    dataset: Dataset,
) -> None:
    transfer_1 = FailingTransfer()
    transfer_2 = FailingTransfer()
    transfer = SelectFileTransfer([transfer_1, transfer_2])

    with pytest.raises(RuntimeError, match="no suitable file transfer available"):
        with transfer.connect_for_upload(dataset, RemotePath("file")):
            ...


def test_select_upload_fails_if_upload_fails_after_connection(
    dataset: Dataset,
) -> None:
    transfer_1 = FailingDuringTransfer()
    transfer = SelectFileTransfer([transfer_1])

    file = File.from_local("local_file", remote_path="remote_file")
    with transfer.connect_for_upload(dataset, RemotePath("file")) as con:
        assert transfer_1.is_open_for_upload
        with pytest.raises(RuntimeError, match="This should propagate to the user"):
            con.upload_files(file)
    assert not transfer_1.is_open_for_upload


def test_select_upload_uses_first_child_transfer_success(dataset: Dataset) -> None:
    transfer_1 = SuccessfulTransfer()
    transfer_2 = FailingTransfer()
    transfer = SelectFileTransfer([transfer_1, transfer_2])

    file = File.from_local("local_file", remote_path="remote_file")
    with transfer.connect_for_upload(dataset, RemotePath("remote_file")) as con:
        con.upload_files(file)

    assert not transfer_1.is_open_for_download
    assert transfer_1.uploaded == [file.local_path]
    assert not transfer_1.downloaded
    assert not transfer_1.reverted


def test_select_upload_uses_second_child_transfer_success(dataset: Dataset) -> None:
    transfer_1 = FailingTransfer()
    transfer_2 = SuccessfulTransfer()
    transfer = SelectFileTransfer([transfer_1, transfer_2])

    file = File.from_local("local_file", remote_path="remote_file")
    with transfer.connect_for_upload(dataset, RemotePath("remote_file")) as con:
        con.upload_files(file)

    assert not transfer_2.is_open_for_download
    assert transfer_2.uploaded == [file.local_path]
    assert not transfer_2.downloaded
    assert not transfer_2.reverted


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Copy and link transfers do not support Windows",
)
@pytest.mark.parametrize("hard_link", [True, False])
def test_copy_and_link_transfers_fall_back(dataset: Dataset, hard_link: bool) -> None:
    copier = CopyFileTransfer(hard_link=hard_link)
    linker = LinkFileTransfer()
    fallback = SuccessfulTransfer()
    transfer = SelectFileTransfer([copier, linker, fallback])

    file = File.from_local("/not-a-real-parent/local_file", remote_path="remote_file")
    with transfer.connect_for_upload(dataset, RemotePath("remote_file")) as con:
        con.upload_files(file)

    assert not fallback.is_open_for_download
    assert fallback.uploaded == [file.local_path]
    assert not fallback.downloaded
    assert not fallback.reverted
