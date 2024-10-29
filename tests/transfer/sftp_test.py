# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="no-untyped-def, return-value, arg-type, union-attr"

import dataclasses
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import paramiko
import pytest

from scitacean import Dataset, File, RemotePath
from scitacean.testing.client import FakeClient
from scitacean.testing.sftp import IgnorePolicy, skip_if_not_sftp
from scitacean.transfer.sftp import (
    SFTPDownloadConnection,
    SFTPFileTransfer,
    SFTPUploadConnection,
)


@pytest.fixture(scope="session", autouse=True)
def _server(request, sftp_fileserver) -> None:
    skip_if_not_sftp(request)


def test_download_one_file(
    sftp_access, sftp_connect_with_username_password, tmp_path
) -> None:
    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_download() as con:
        con.download_files(
            remote=[RemotePath("/data/seed/text.txt")], local=[tmp_path / "text.txt"]
        )
    assert (
        tmp_path.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )


def test_download_two_files(
    sftp_access, sftp_connect_with_username_password, tmp_path
) -> None:
    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_download() as con:
        con.download_files(
            remote=[
                RemotePath("/data/seed/table.csv"),
                RemotePath("/data/seed/text.txt"),
            ],
            local=[tmp_path / "local-table.csv", tmp_path / "text.txt"],
        )
    assert tmp_path.joinpath("local-table.csv").read_text() == "7,2\n5,2\n"
    assert (
        tmp_path.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )


def test_upload_one_file_source_folder_in_dataset(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/upload"))
    tmp_path.joinpath("file0.txt").write_text("File to test upload123")

    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        assert con.source_folder == RemotePath("/data/upload")
        con.upload_files(
            File.from_local(path=tmp_path / "file0.txt", remote_path="upload_0.txt")
        )

    assert (
        sftp_data_dir.joinpath("upload", "upload_0.txt").read_text()
        == "File to test upload123"
    )


def test_upload_one_file_source_folder_in_transfer(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", owner="librarian")
    tmp_path.joinpath("file1.txt").write_text("File no. 2")

    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        source_folder="/data/upload/{owner}",
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        assert con.source_folder == RemotePath("/data/upload/librarian")
        con.upload_files(
            File.from_local(
                path=tmp_path / "file1.txt", remote_path=RemotePath("upload_1.txt")
            )
        )

    assert (
        sftp_data_dir.joinpath("upload", "librarian", "upload_1.txt").read_text()
        == "File no. 2"
    )


def test_upload_two_files(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/upload2"))
    tmp_path.joinpath("file2.1.md").write_text("First part of file 2")
    tmp_path.joinpath("file2.2.md").write_text("Second part of file 2")

    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        assert con.source_folder == RemotePath("/data/upload2")
        con.upload_files(
            File.from_local(path=tmp_path / "file2.1.md", base_path=tmp_path),
            File.from_local(path=tmp_path / "file2.2.md", base_path=tmp_path),
        )

    assert (
        sftp_data_dir.joinpath("upload2", "file2.1.md").read_text()
        == "First part of file 2"
    )
    assert (
        sftp_data_dir.joinpath("upload2", "file2.2.md").read_text()
        == "Second part of file 2"
    )


def test_upload_one_file_existing_source_folder(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/upload-multiple"))
    tmp_path.joinpath("file3.1.md").write_text("First part of file 3")
    tmp_path.joinpath("file3.2.md").write_text("Second part of file 3")

    # First upload to ensure the folder exists.
    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        assert con.source_folder == RemotePath("/data/upload-multiple")
        con.upload_files(
            File.from_local(path=tmp_path / "file3.1.md", base_path=tmp_path),
        )

    # Second upload to test uploading to existing folder.
    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        assert con.source_folder == RemotePath("/data/upload-multiple")
        con.upload_files(
            File.from_local(path=tmp_path / "file3.2.md", base_path=tmp_path),
        )

    assert (
        sftp_data_dir.joinpath("upload-multiple", "file3.1.md").read_text()
        == "First part of file 3"
    )
    assert (
        sftp_data_dir.joinpath("upload-multiple", "file3.2.md").read_text()
        == "Second part of file 3"
    )


def test_revert_all_uploaded_files_single(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/revert-all-test-1"))
    tmp_path.joinpath("file3.txt").write_text("File that should get reverted")

    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        file = File.from_local(path=tmp_path / "file3.txt", base_path=tmp_path)
        con.upload_files(file)
        con.revert_upload(file)

    assert "revert-all-test-1" not in (p.name for p in sftp_data_dir.iterdir())


def test_revert_all_uploaded_files_two(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/revert-all-test-2"))
    tmp_path.joinpath("file3.1.txt").write_text("File that should get reverted 1")
    tmp_path.joinpath("file3.2.txt").write_text("File that should get reverted 2")

    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        file1 = File.from_local(path=tmp_path / "file3.1.txt", base_path=tmp_path)
        file2 = File.from_local(path=tmp_path / "file3.2.txt", base_path=tmp_path)
        con.upload_files(file1, file2)
        con.revert_upload(file1, file2)

    assert "revert-all-test-2" not in (p.name for p in sftp_data_dir.iterdir())


def test_revert_one_uploaded_file(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/revert-test"))
    tmp_path.joinpath("file4.txt").write_text("File that should get reverted")
    tmp_path.joinpath("file5.txt").write_text("File that should be kept")

    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        file4 = File.from_local(path=tmp_path / "file4.txt", base_path=tmp_path)
        file5 = File.from_local(path=tmp_path / "file5.txt", base_path=tmp_path)
        con.upload_files(file4, file5)
        con.revert_upload(file4)

    assert "file4.txt" not in (
        p.name for p in (sftp_data_dir / "revert-test").iterdir()
    )
    assert (
        sftp_data_dir.joinpath("revert-test", "file5.txt").read_text()
        == "File that should be kept"
    )


def test_stat_uploaded_file(
    sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/upload6"))
    tmp_path.joinpath("file6.txt").write_text("File to test upload no 6")

    sftp = SFTPFileTransfer(
        host=sftp_access.host,
        port=sftp_access.port,
        connect=sftp_connect_with_username_password,
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        [uploaded] = con.upload_files(
            File.from_local(path=tmp_path / "file6.txt", remote_path="upload_6.txt")
        )

    st = (sftp_data_dir / "upload6" / "upload_6.txt").stat()
    assert uploaded.size == st.st_size

    # Set in docker-compose
    assert uploaded.remote_uid == "1000"
    assert uploaded.remote_gid == "1000"

    uploaded = dataclasses.replace(uploaded, local_path=None)
    assert datetime.now(tz=timezone.utc) - uploaded.creation_time < timedelta(seconds=5)


class CorruptingSFTP(paramiko.SFTPClient):
    """Appends bytes to uploaded files to simulate a broken transfer."""

    def put(
        self, localpath, remotepath, callback=None, confirm=True
    ) -> paramiko.SFTPAttributes:
        with open(localpath) as f:
            content = f.read()
        with tempfile.TemporaryDirectory() as tempdir:
            corrupted_path = Path(tempdir) / "corrupted"
            with open(corrupted_path, "w") as f:
                f.write(content + "\nevil bytes")
            return super().put(str(corrupted_path), remotepath, callback, confirm)


class CorruptingTransfer(paramiko.Transport):
    """Uses CorruptingSFTP to simulate a broken connection."""

    def open_sftp_client(self) -> paramiko.SFTPClient:
        return CorruptingSFTP.from_transport(self)


@pytest.fixture
def sftp_corrupting_connect(sftp_access, sftp_connection_config) -> None:
    def connect(host: str, port: int) -> paramiko.SFTPClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(IgnorePolicy())
        client.connect(
            hostname=host,
            port=port,
            username=sftp_access.user.username,
            password=sftp_access.user.password,
            allow_agent=False,
            look_for_keys=False,
            transport_factory=CorruptingTransfer,
        )
        return client.open_sftp()

    return connect


class RaisingSFTP(paramiko.SFTPClient):
    def put(
        self, localpath, remotepath, callback=None, confirm=True
    ) -> paramiko.SFTPAttributes:
        raise RuntimeError("Upload disabled")


class RaisingTransfer(paramiko.Transport):
    def open_sftp_client(self) -> paramiko.SFTPClient:
        return RaisingSFTP.from_transport(self)


@pytest.fixture
def sftp_raising_connect(sftp_access) -> None:
    def connect(host: str, port: int) -> paramiko.SFTPClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(IgnorePolicy())
        client.connect(
            hostname=host,
            port=port,
            username=sftp_access.user.username,
            password=sftp_access.user.password,
            allow_agent=False,
            look_for_keys=False,
            transport_factory=RaisingTransfer,
        )
        return client.open_sftp()

    return connect


def test_upload_file_reverts_if_upload_fails(
    sftp_access, sftp_raising_connect, tmp_path, sftp_data_dir
):
    ds = Dataset(type="raw", source_folder=RemotePath("/data/upload8"))
    tmp_path.joinpath("file8.txt").write_text("File to test upload no 8")

    sftp = SFTPFileTransfer(
        host=sftp_access.host, port=sftp_access.port, connect=sftp_raising_connect
    )
    with sftp.connect_for_upload(dataset=ds) as con:
        with pytest.raises(RuntimeError):
            con.upload_files(
                File.from_local(
                    path=tmp_path / "file8.txt",
                    remote_path=RemotePath("upload_8.txt"),
                )
            )

    assert "upload8" not in (p.name for p in sftp_data_dir.iterdir())


class SFTPTestFileTransfer(SFTPFileTransfer):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @contextmanager
    def connect_for_download(self) -> Iterator[SFTPDownloadConnection]:
        with super().connect_for_download() as connection:
            yield connection

    @contextmanager
    def connect_for_upload(self, dataset: Dataset) -> Iterator[SFTPUploadConnection]:
        with super().connect_for_upload(dataset=dataset) as connection:
            yield connection


# This test is referenced in the docs.
def test_client_with_sftp(
    require_sftp_fileserver,
    sftp_access,
    sftp_connect_with_username_password,
    sftp_data_dir,
    tmp_path,
):
    tmp_path.joinpath("file1.txt").write_text("File contents")

    client = FakeClient.without_login(
        url="",
        file_transfer=SFTPTestFileTransfer(
            connect=sftp_connect_with_username_password,
            host=sftp_access.host,
            port=sftp_access.port,
        ),
    )
    ds = Dataset(
        access_groups=["group1"],
        contact_email="p.stibbons@uu.am",
        creation_location="UU",
        creation_time=datetime(2023, 6, 23, 10, 0, 0, tzinfo=timezone.utc),
        name="Secret Thaum Storage",
        owner="PonderStibbons",
        owner_group="uu",
        principal_investigator="MustrumRidcully",
        source_folder="/data",
        type="raw",
    )
    ds.add_local_files(tmp_path / "file1.txt", base_path=tmp_path)
    finalized = client.upload_new_dataset_now(ds)

    downloaded = client.get_dataset(finalized.pid)
    downloaded = client.download_files(downloaded, target=tmp_path / "download")

    assert sftp_data_dir.joinpath("file1.txt").read_text() == "File contents"
    assert downloaded.files[0].local_path.read_text() == "File contents"
