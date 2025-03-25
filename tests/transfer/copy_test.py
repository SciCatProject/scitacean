# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from scitacean import (
    PID,
    Dataset,
    DatasetType,
    File,
    FileNotAccessibleError,
    RemotePath,
)
from scitacean.model import DownloadDataFile, DownloadDataset, DownloadOrigDatablock
from scitacean.testing.client import FakeClient
from scitacean.transfer.copy import CopyFileTransfer

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
    copier = CopyFileTransfer()
    with copier.connect_for_download(dataset, RemotePath.from_local(tmp_path)) as con:
        con.download_files(
            remote=[RemotePath(str(remote_dir / "text.txt"))],
            local=[local_dir / "text.txt"],
        )
    assert (
        local_dir.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )
    assert not local_dir.joinpath("text.txt").is_symlink()


def test_download_two_files(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("table.csv").write_text("7,2\n5,2\n")
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    dataset.source_folder = RemotePath.from_local(remote_dir)
    copier = CopyFileTransfer()
    with copier.connect_for_download(dataset, RemotePath.from_local(tmp_path)) as con:
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


def test_download_makes_a_copy(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    dataset.source_folder = RemotePath.from_local(remote_dir)
    copier = CopyFileTransfer()
    with copier.connect_for_download(dataset, RemotePath.from_local(tmp_path)) as con:
        con.download_files(
            remote=[RemotePath(str(remote_dir / "text.txt"))],
            local=[local_dir / "text.txt"],
        )
    assert not local_dir.joinpath("text.txt").is_symlink()


def test_download_with_hard_link(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("text.txt").write_text("This is some text for testing.\n")
    local_dir = tmp_path / "user"
    local_dir.mkdir()

    dataset.source_folder = RemotePath.from_local(remote_dir)
    copier = CopyFileTransfer(hard_link=True)
    with copier.connect_for_download(dataset, RemotePath.from_local(tmp_path)) as con:
        con.download_files(
            remote=[RemotePath(str(remote_dir / "text.txt"))],
            local=[local_dir / "text.txt"],
        )
    assert (
        local_dir.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )
    assert not local_dir.joinpath("text.txt").is_symlink()

    local_dir.joinpath("text.txt").write_text("New content")
    assert remote_dir.joinpath("text.txt").read_text() == "New content"


def test_upload_one_file(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"

    local_dir = tmp_path / "user"
    local_dir.mkdir()
    local_dir.joinpath("text.txt").write_text("This is some text for testing.\n")

    dataset.source_folder = RemotePath.from_local(remote_dir)
    copier = CopyFileTransfer()
    with copier.connect_for_upload(dataset, RemotePath.from_local(tmp_path)) as con:
        assert con.source_folder == dataset.source_folder
        con.upload_files(
            File.from_local(path=local_dir / "text.txt", remote_path="text.txt")
        )
    assert (
        remote_dir.joinpath("text.txt").read_text()
        == "This is some text for testing.\n"
    )
    assert not remote_dir.joinpath("text.txt").is_symlink()


def test_upload_with_hard_link(tmp_path: Path, dataset: Dataset) -> None:
    remote_dir = tmp_path / "server"

    local_dir = tmp_path / "user"
    local_dir.mkdir()
    local_dir.joinpath("text.txt").write_text("This is some text for testing.\n")

    dataset.source_folder = RemotePath.from_local(remote_dir)
    copier = CopyFileTransfer(hard_link=True)
    with copier.connect_for_upload(dataset, RemotePath.from_local(tmp_path)) as con:
        assert con.source_folder == dataset.source_folder
        con.upload_files(
            File.from_local(path=local_dir / "text.txt", remote_path="text.txt")
        )
    assert (
        remote_dir.joinpath("text.txt").read_text()
        == "This is some text for testing.\n"
    )
    assert not remote_dir.joinpath("text.txt").is_symlink()

    remote_dir.joinpath("text.txt").write_text("New content")
    assert local_dir.joinpath("text.txt").read_text() == "New content"


def test_revert_one_uploaded_file(
    tmp_path: Path,
    dataset: Dataset,
) -> None:
    remote_dir = tmp_path / "server"

    local_dir = tmp_path / "user"
    local_dir.mkdir()
    local_dir.joinpath("file1").write_text("File that should get reverted")
    local_dir.joinpath("file2").write_text("File that should be kept")

    dataset.source_folder = RemotePath.from_local(remote_dir)
    copier = CopyFileTransfer()
    with copier.connect_for_upload(dataset, RemotePath.from_local(tmp_path)) as con:
        file1 = File.from_local(path=local_dir / "file1")
        file2 = File.from_local(path=local_dir / "file2")
        con.upload_files(file1, file2)
        con.revert_upload(file1)

    assert "file1" not in (p.name for p in remote_dir.iterdir())
    assert remote_dir.joinpath("file2").read_text() == "File that should be kept"


def test_copy_transfer_raises_if_file_does_not_exist(
    fs: FakeFilesystem, dataset: Dataset
) -> None:
    fs.create_dir("data")

    dataset.source_folder = RemotePath("")
    copier = CopyFileTransfer()
    with copier.connect_for_download(dataset, RemotePath("data")) as con:
        with pytest.raises(FileNotAccessibleError) as exc_info:
            con.download_files(
                remote=[RemotePath("data/non_existent.txt")],
                local=[Path("non_existent.txt")],
            )
    assert exc_info.value.remote_path == "data/non_existent.txt"


def test_copy_transfer_connect_raises_if_folder_does_not_exist(
    fs: FakeFilesystem, dataset: Dataset
) -> None:
    dataset.source_folder = RemotePath("")
    copier = CopyFileTransfer()
    with pytest.raises(FileNotAccessibleError) as exc_info:
        with copier.connect_for_download(dataset, RemotePath("data")):
            ...
    assert exc_info.value.remote_path == "data"


def test_client_download_with_copy(tmp_path: Path) -> None:
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

    client = FakeClient.without_login(url="", file_transfer=CopyFileTransfer())
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


def test_client_download_with_copy_local_file_exists(tmp_path: Path) -> None:
    content = "This is some text for testing.\n"
    checksum = hashlib.md5(content.encode("utf-8")).hexdigest()
    remote_dir = tmp_path / "server"
    remote_dir.mkdir()
    remote_dir.joinpath("file1.txt").write_text(content)

    local_dir = tmp_path / "download"
    local_dir.mkdir()
    local_dir.joinpath("file1.txt").symlink_to(remote_dir / "file1.txt")

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

    client = FakeClient.without_login(url="", file_transfer=CopyFileTransfer())
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
    assert local_dir.joinpath("file1.txt").is_symlink()


def test_client_upload_with_copy(tmp_path: Path) -> None:
    content = "This is some text for testing.\n"
    local_dir = tmp_path / "user"
    local_dir.mkdir()
    local_dir.joinpath("file1.txt").write_text(content)

    remote_dir = tmp_path / "server"

    ds = Dataset(
        access_groups=["group1"],
        contact_email="p.stibbons@uu.am",
        creation_location="UU",
        owner="PonderStibbons",
        owner_group="uu",
        principal_investigator="MustrumRidcully",
        source_folder=RemotePath.from_local(remote_dir),
        type=DatasetType.RAW,
    )
    ds.add_local_files(local_dir / "file1.txt")

    client = FakeClient.without_login(url="", file_transfer=CopyFileTransfer())
    client.upload_new_dataset_now(ds)

    assert remote_dir.joinpath("file1.txt").read_text() == content
