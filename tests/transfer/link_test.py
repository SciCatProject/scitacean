# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Scitacean contributors (https://github.com/SciCatProject/scitacean)

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scitacean import PID, Dataset, DatasetType, RemotePath
from scitacean.model import DownloadDataFile, DownloadDataset, DownloadOrigDatablock
from scitacean.testing.client import FakeClient
from scitacean.transfer.link import LinkFileTransfer

if sys.platform.startswith("win"):
    pytest.skip("LinkFileTransfer does not work on Windows", allow_module_level=True)


def test_download_one_file(tmp_path: Path) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    linker = LinkFileTransfer()
    with linker.connect_for_download() as con:
        con.download_files(
            remote=[RemotePath(str(remote_dir / "text.txt"))],
            local=[local_dir / "text.txt"],
        )
    assert (
        local_dir.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )


def test_download_two_files(tmp_path: Path) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("table.csv").write_text("7,2\n5,2\n")
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    linker = LinkFileTransfer()
    with linker.connect_for_download() as con:
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


def test_link_transfer_cannot_upload() -> None:
    ds = Dataset(type="raw", source_folder=RemotePath("/data/upload"))
    linker = LinkFileTransfer()
    with pytest.raises(NotImplementedError):
        linker.connect_for_upload(ds)


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


def test_client_with_link_local_file_exists_clashing_content(tmp_path: Path) -> None:
    content = "This is some text for testing.\n"
    checksum = hashlib.md5(content.encode("utf-8")).hexdigest()
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("file1.txt").write_text(content)

    local_dir = tmp_path / "download"
    local_dir.mkdir()
    local_dir.joinpath("file1.txt").write_text(content + content)

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
    with pytest.raises(FileExistsError):
        # We do not overwrite existing files
        client.download_files(downloaded, target=local_dir)


def test_download_file_does_not_exist(tmp_path: Path) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    linker = LinkFileTransfer()
    with linker.connect_for_download() as con:
        with pytest.raises(FileNotFoundError):
            con.download_files(
                remote=[RemotePath(str(remote_dir / "text.txt"))],
                local=[local_dir / "text.txt"],
            )
