# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from scitacean import PID, Dataset, DatasetType, FileNotAccessibleError, RemotePath
from scitacean.model import DownloadDataFile, DownloadDataset, DownloadOrigDatablock
from scitacean.testing.client import FakeClient
from scitacean.transfer.link import LinkFileTransfer

if sys.platform.startswith("win"):
    pytest.skip("LinkFileTransfer does not work on Windows", allow_module_level=True)


@pytest.fixture
def dataset() -> Dataset:
    return Dataset(type="raw")


def test_download_one_file(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    dataset.source_folder = RemotePath.from_local(remote_dir)
    linker = LinkFileTransfer()
    with linker.connect_for_download(dataset, RemotePath.from_local(tmp_path)) as con:
        con.download_files(
            remote=[RemotePath(str(remote_dir / "text.txt"))],
            local=[local_dir / "text.txt"],
        )
    assert (
        local_dir.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )


def test_download_two_files(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("table.csv").write_text("7,2\n5,2\n")
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    dataset.source_folder = RemotePath.from_local(remote_dir)
    linker = LinkFileTransfer()
    with linker.connect_for_download(dataset, RemotePath.from_local(tmp_path)) as con:
        con.download_files(
            remote=[
                RemotePath(str(remote_dir / "table.csv")),
                RemotePath(str(remote_dir / "text.txt")),
            ],
            local=[local_dir / "local-table.csv", local_dir / "text.txt"],
        )
    assert local_dir.joinpath("local-table.csv").read_text() == "7,2\n5,2\n"
    assert (
        local_dir.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )


def test_link_transfer_creates_symlink(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    dataset.source_folder = RemotePath.from_local(remote_dir)
    linker = LinkFileTransfer()
    with linker.connect_for_download(dataset, RemotePath.from_local(tmp_path)) as con:
        con.download_files(
            remote=[RemotePath(str(remote_dir / "text.txt"))],
            local=[local_dir / "text.txt"],
        )
    assert local_dir.joinpath("text.txt").is_symlink()


def test_link_transfer_cannot_upload() -> None:
    ds = Dataset(type="raw", source_folder=RemotePath("/data/upload"))
    linker = LinkFileTransfer()
    with pytest.raises(NotImplementedError):
        with linker.connect_for_upload(ds, cast(RemotePath, ds.source_folder)):
            ...


def test_link_transfer_raises_if_file_does_not_exist(
    fs: FakeFilesystem, dataset: Dataset
) -> None:
    fs.create_dir("data")

    dataset.source_folder = RemotePath("")
    linker = LinkFileTransfer()
    with linker.connect_for_download(dataset, RemotePath("data")) as con:
        with pytest.raises(FileNotAccessibleError) as exc_info:
            con.download_files(
                remote=[RemotePath("data/non_existent.txt")],
                local=[Path("non_existent.txt")],
            )
    assert exc_info.value.remote_path == "data/non_existent.txt"


def test_link_transfer_connect_raises_if_folder_does_not_exist(
    fs: FakeFilesystem, dataset: Dataset
) -> None:
    dataset.source_folder = RemotePath("")
    linker = LinkFileTransfer()
    with pytest.raises(FileNotAccessibleError) as exc_info:
        with linker.connect_for_download(dataset, RemotePath("data")):
            ...
    assert exc_info.value.remote_path == "data"


def test_client_with_link(tmp_path: Path) -> None:
    content = "This is some text for testing.\n"
    checksum = hashlib.md5(content.encode("utf-8")).hexdigest()
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("file1.txt").write_text(content)

    ds = DownloadDataset(
        accessGroups=["group1"],
        contactEmail="p.stibbons@uu.am",
        creationLocation="UU",
        creationTime=datetime(2023, 6, 23, 10, 0, 0, tzinfo=timezone.utc),
        numberOfFiles=1,
        numberOfFilesArchived=0,
        owner="PonderStibbons",
        ownerGroup="uu",
        pid=PID(prefix="UU.0123", pid="1234567890"),
        principalInvestigator="MustrumRidcully",
        size=len(content),
        sourceFolder=RemotePath(str(remote_dir)),
        type=DatasetType.RAW,
    )
    db = DownloadOrigDatablock(
        dataFileList=[
            DownloadDataFile(
                path="file1.txt",
                size=len(content),
                chk=checksum,
                time=datetime(2023, 6, 23, 10, 0, 0, tzinfo=timezone.utc),
            )
        ],
        datasetId=ds.pid,
        size=len(content),
        chkAlg="md5",
    )

    client = FakeClient.without_login(
        url="",
        file_transfer=LinkFileTransfer(),
    )
    client.datasets[PID(prefix="UU.0123", pid="1234567890")] = ds
    client.orig_datablocks[PID(prefix="UU.0123", pid="1234567890")] = [db]

    downloaded = client.get_dataset(PID(prefix="UU.0123", pid="1234567890"))
    downloaded = client.download_files(downloaded, target=tmp_path / "download")

    assert (
        tmp_path.joinpath("download", "file1.txt").read_text()
        == "This is some text for testing.\n"
    )
    assert (
        downloaded.files[0].local_path.read_text() == "This is some text for testing.\n"  # type: ignore[union-attr]
    )


def test_client_with_link_local_file_exists(tmp_path: Path) -> None:
    content = "This is some text for testing.\n"
    checksum = hashlib.md5(content.encode("utf-8")).hexdigest()
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("file1.txt").write_text(content)

    local_dir = tmp_path / "download"
    local_dir.mkdir()
    local_dir.joinpath("file1.txt").write_text(content)

    ds = DownloadDataset(
        accessGroups=["group1"],
        contactEmail="p.stibbons@uu.am",
        creationLocation="UU",
        creationTime=datetime(2023, 6, 23, 10, 0, 0, tzinfo=timezone.utc),
        numberOfFiles=1,
        numberOfFilesArchived=0,
        owner="PonderStibbons",
        ownerGroup="uu",
        pid=PID(prefix="UU.0123", pid="1234567890"),
        principalInvestigator="MustrumRidcully",
        size=len(content),
        sourceFolder=RemotePath(str(remote_dir)),
        type=DatasetType.RAW,
    )
    db = DownloadOrigDatablock(
        dataFileList=[
            DownloadDataFile(
                path="file1.txt",
                size=len(content),
                chk=checksum,
                time=datetime(2023, 6, 23, 10, 0, 0, tzinfo=timezone.utc),
            )
        ],
        datasetId=ds.pid,
        size=len(content),
        chkAlg="md5",
    )

    client = FakeClient.without_login(
        url="",
        file_transfer=LinkFileTransfer(),
    )
    client.datasets[PID(prefix="UU.0123", pid="1234567890")] = ds
    client.orig_datablocks[PID(prefix="UU.0123", pid="1234567890")] = [db]

    downloaded = client.get_dataset(PID(prefix="UU.0123", pid="1234567890"))
    downloaded = client.download_files(downloaded, target=local_dir)

    assert (
        local_dir.joinpath("file1.txt").read_text()
        == "This is some text for testing.\n"
    )
    assert (
        downloaded.files[0].local_path.read_text() == "This is some text for testing.\n"  # type: ignore[union-attr]
    )
    # Existing file was not overwritten
    assert not local_dir.joinpath("file1.txt").is_symlink()
