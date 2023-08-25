# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="no-untyped-def, return-value, arg-type, union-attr"

import dataclasses
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator, Optional

import fabric
import paramiko
import pytest
from fabric import Connection

from scitacean import Dataset, File, FileUploadError, RemotePath
from scitacean.testing.client import FakeClient
from scitacean.testing.sftp import IgnorePolicy, skip_if_not_sftp
from scitacean.transfer.sftp import (
    SFTPDownloadConnection,
    SFTPFileTransfer,
    SFTPUploadConnection,
)


@pytest.fixture(scope="session", autouse=True)
def server(request, sftp_fileserver):
    skip_if_not_sftp(request)


def test_download_one_file(sftp_access, sftp_connect_with_username_password, tmp_path):
    sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
    with sftp.connect_for_download(connect=sftp_connect_with_username_password) as con:
        con.download_files(
            remote=[RemotePath("/data/seed/text.txt")], local=[tmp_path / "text.txt"]
        )
    assert (
        tmp_path.joinpath("text.txt").read_text() == "This is some text for testing.\n"
    )


def test_download_two_files(sftp_access, sftp_connect_with_username_password, tmp_path):
    sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
    with sftp.connect_for_download(connect=sftp_connect_with_username_password) as con:
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

    sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
    with sftp.connect_for_upload(
        dataset=ds, connect=sftp_connect_with_username_password
    ) as con:
        assert con.source_folder == RemotePath("/data/upload")
        con.upload_files(
            File.from_local(path=tmp_path / "file0.txt", remote_path="upload_0.txt")
        )

    assert (
        sftp_data_dir.joinpath("upload", "upload_0.txt").read_text()
        == "File to test upload123"
    )


# def test_upload_one_file_source_folder_in_transfer(
#     sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(type="raw", owner="librarian")
#     with open(tmp_path / "file1.txt", "w") as f:
#         f.write("File no. 2")
#
#     sftp = SFTPFileTransfer(
#         host=sftp_access.host,
#         port=sftp_access.port,
#         source_folder="/data/upload/{owner}",
#     )
#     with sftp.connect_for_upload(
#         dataset=ds, connect=sftp_connect_with_username_password
#     ) as con:
#         assert con.source_folder == RemotePath("/data/upload/librarian")
#         con.upload_files(
#             File.from_local(
#                 path=tmp_path / "file1.txt", remote_path=RemotePath("upload_1.txt")
#             )
#         )
#
#     with open(sftp_data_dir / "upload" / "librarian" / "upload_1.txt", "r") as f:
#         assert f.read() == "File no. 2"
#
#
# def test_upload_two_files(
#     sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(type="raw", source_folder=RemotePath("/data/upload2"))
#     with open(tmp_path / "file2.1.md", "w") as f:
#         f.write("First part of file 2")
#     with open(tmp_path / "file2.2.md", "w") as f:
#         f.write("Second part of file 2")
#
#     sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
#     with sftp.connect_for_upload(
#         dataset=ds, connect=sftp_connect_with_username_password
#     ) as con:
#         assert con.source_folder == RemotePath("/data/upload2")
#         con.upload_files(
#             File.from_local(path=tmp_path / "file2.1.md", base_path=tmp_path),
#             File.from_local(path=tmp_path / "file2.2.md", base_path=tmp_path),
#         )
#
#     with open(sftp_data_dir / "upload2" / "file2.1.md", "r") as f:
#         assert f.read() == "First part of file 2"
#     with open(sftp_data_dir / "upload2" / "file2.2.md", "r") as f:
#         assert f.read() == "Second part of file 2"
#
#
# def test_revert_all_uploaded_files_single(
#     sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(type="raw", source_folder=RemotePath("/data/revert-all-test-1"))
#     with open(tmp_path / "file3.txt", "w") as f:
#         f.write("File that should get reverted")
#
#     sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
#     with sftp.connect_for_upload(
#         dataset=ds, connect=sftp_connect_with_username_password
#     ) as con:
#         file = File.from_local(path=tmp_path / "file3.txt", base_path=tmp_path)
#         con.upload_files(file)
#         con.revert_upload(file)
#
#     assert "revert-all-test-1" not in (p.name for p in sftp_data_dir.iterdir())
#
#
# def test_revert_all_uploaded_files_two(
#     sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(type="raw", source_folder=RemotePath("/data/revert-all-test-2"))
#     with open(tmp_path / "file3.1.txt", "w") as f:
#         f.write("File that should get reverted 1")
#     with open(tmp_path / "file3.2.txt", "w") as f:
#         f.write("File that should get reverted 2")
#
#     sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
#     with sftp.connect_for_upload(
#         dataset=ds, connect=sftp_connect_with_username_password
#     ) as con:
#         file1 = File.from_local(path=tmp_path / "file3.1.txt", base_path=tmp_path)
#         file2 = File.from_local(path=tmp_path / "file3.2.txt", base_path=tmp_path)
#         con.upload_files(file1, file2)
#         con.revert_upload(file1, file2)
#
#     assert "revert-all-test-2" not in (p.name for p in sftp_data_dir.iterdir())
#
#
# def test_revert_one_uploaded_file(
#     sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(type="raw", source_folder=RemotePath("/data/revert-test"))
#     with open(tmp_path / "file4.txt", "w") as f:
#         f.write("File that should get reverted")
#     with open(tmp_path / "file5.txt", "w") as f:
#         f.write("File that should be kept")
#
#     sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
#     with sftp.connect_for_upload(
#         dataset=ds, connect=sftp_connect_with_username_password
#     ) as con:
#         file4 = File.from_local(path=tmp_path / "file4.txt", base_path=tmp_path)
#         file5 = File.from_local(path=tmp_path / "file5.txt", base_path=tmp_path)
#         con.upload_files(file4, file5)
#         con.revert_upload(file4)
#
#     assert "file4.txt" not in (p.name for p in (sftp_data_dir / "revert-test").iterdir())
#     with open(sftp_data_dir / "revert-test" / "file5.txt", "r") as f:
#         assert f.read() == "File that should be kept"
#
#
# def test_stat_uploaded_file(
#     sftp_access, sftp_connect_with_username_password, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(type="raw", source_folder=RemotePath("/data/upload6"))
#     with open(tmp_path / "file6.txt", "w") as f:
#         f.write("File to test upload no 6")
#
#     sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
#     with sftp.connect_for_upload(
#         dataset=ds, connect=sftp_connect_with_username_password
#     ) as con:
#         [uploaded] = con.upload_files(
#             File.from_local(path=tmp_path / "file6.txt", remote_path="upload_6.txt")
#         )
#
#     st = (sftp_data_dir / "upload6" / "upload_6.txt").stat()
#     assert uploaded.size == st.st_size
#
#     # Set in docker-compose
#     assert uploaded.remote_uid == "1000"
#     assert uploaded.remote_gid == "1000"
#
#     uploaded = dataclasses.replace(uploaded, local_path=None)
#     assert datetime.now(tz=timezone.utc) - uploaded.creation_time < timedelta(seconds=5)
#
#
# class CorruptingSFTP(paramiko.SFTPClient):
#     """Appends bytes to uploaded files to simulate a broken transfer."""
#
#     def put(self, localpath, remotepath, callback=None, confirm=True):
#         with open(localpath, "r") as f:
#             content = f.read()
#         with tempfile.TemporaryDirectory() as tempdir:
#             corrupted_path = Path(tempdir) / "corrupted"
#             with open(corrupted_path, "w") as f:
#                 f.write(content + "\nevil bytes")
#             super().put(str(corrupted_path), remotepath, callback, confirm)
#
#
# class CorruptingTransfer(paramiko.Transport):
#     """Uses CorruptingSFTP to simulate a broken connection."""
#
#     def open_sftp_client(self) -> paramiko.SFTPClient:
#         return CorruptingSFTP.from_transport(self)
#
#
# @pytest.fixture()
# def sftp_corrupting_connect(sftp_access, sftp_connection_config):
#     def connect(host: str, port: int, **kwargs):
#         if kwargs:
#             raise ValueError(
#                 "connect_with_username_password must only be"
#                 f" used without extra arguments. Got {kwargs=}"
#             )
#         connection = fabric.Connection(
#             host=host,
#             port=port,
#             user=sftp_access.user.username,
#             config=sftp_connection_config,
#             connect_kwargs={
#                 "password": sftp_access.user.password,
#                 "transport_factory": CorruptingTransfer,
#                 **sftp_connection_config.connect_kwargs,
#             },
#         )
#         connection.client.set_missing_host_key_policy(IgnorePolicy())
#         return connection
#
#     return connect
#
#
# def test_upload_file_detects_checksum_mismatch(
#     sftp_access, sftp_corrupting_connect, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(
#         type="raw",
#         source_folder=RemotePath("/data/upload7"),
#         checksum_algorithm="blake2b",
#     )
#     with open(tmp_path / "file7.txt", "w") as f:
#         f.write("File to test upload no 7")
#
#     sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
#     with sftp.connect_for_upload(dataset=ds, connect=sftp_corrupting_connect) as con:
#         with pytest.raises(FileUploadError):
#             con.upload_files(
#                 dataclasses.replace(
#                     File.from_local(
#                         path=tmp_path / "file7.txt",
#                         remote_path=RemotePath("upload_7.txt"),
#                     ),
#                     checksum_algorithm="blake2b",
#                 )
#             )
#
#     assert "upload7" not in (p.name for p in sftp_data_dir.iterdir())
#
#
# class RaisingSFTP(paramiko.SFTPClient):
#     def put(self, localpath, remotepath, callback=None, confirm=True):
#         raise RuntimeError("Upload disabled")
#
#
# class RaisingTransfer(paramiko.Transport):
#     def open_sftp_client(self) -> paramiko.SFTPClient:
#         return RaisingSFTP.from_transport(self)
#
#
# @pytest.fixture()
# def sftp_raising_connect(sftp_access, sftp_connection_config):
#     def connect(host: str, port: int, **kwargs):
#         if kwargs:
#             raise ValueError(
#                 "connect_with_username_password must only be"
#                 f" used without extra arguments. Got {kwargs=}"
#             )
#         connection = fabric.Connection(
#             host=host,
#             port=port,
#             user=sftp_access.user.username,
#             config=sftp_connection_config,
#             connect_kwargs={
#                 "password": sftp_access.user.password,
#                 "transport_factory": RaisingTransfer,
#                 **sftp_connection_config.connect_kwargs,
#             },
#         )
#         connection.client.set_missing_host_key_policy(IgnorePolicy())
#         return connection
#
#     return connect
#
#
# def test_upload_file_reverts_if_upload_fails(
#     sftp_access, sftp_raising_connect, tmp_path, sftp_data_dir
# ):
#     ds = Dataset(type="raw", source_folder=RemotePath("/data/upload8"))
#     with open(tmp_path / "file8.txt", "w") as f:
#         f.write("File to test upload no 8")
#
#     sftp = SFTPFileTransfer(host=sftp_access.host, port=sftp_access.port)
#     with sftp.connect_for_upload(dataset=ds, connect=sftp_raising_connect) as con:
#         with pytest.raises(RuntimeError):
#             con.upload_files(
#                 File.from_local(
#                     path=tmp_path / "file8.txt",
#                     remote_path=RemotePath("upload_8.txt"),
#                 )
#             )
#
#     assert "upload8" not in (p.name for p in sftp_data_dir.iterdir())
#
#
# class SFTPTestFileTransfer(SFTPFileTransfer):
#     def __init__(self, connect, **kwargs):
#         super().__init__(**kwargs)
#         self.connect = connect
#
#     @contextmanager
#     def connect_for_download(
#         self, connect: Optional[Callable[..., Connection]] = None
#     ) -> Iterator[SFTPDownloadConnection]:
#         connect = connect if connect is not None else self.connect
#         with super().connect_for_download(connect=connect) as connection:
#             yield connection
#
#     @contextmanager
#     def connect_for_upload(
#         self, dataset: Dataset, connect: Optional[Callable[..., Connection]] = None
#     ) -> Iterator[SFTPUploadConnection]:
#         connect = connect if connect is not None else self.connect
#         with super().connect_for_upload(dataset=dataset, connect=connect) as connection:
#             yield connection
#
#
# # This test is referenced in the docs.
# def test_client_with_sftp(
#     require_sftp_fileserver,
#     sftp_access,
#     sftp_connect_with_username_password,
#     sftp_data_dir,
#     tmp_path,
# ):
#     tmp_path.joinpath("file1.txt").write_text("File contents")
#
#     client = FakeClient.without_login(
#         url="",
#         file_transfer=SFTPTestFileTransfer(
#             connect=sftp_connect_with_username_password,
#             host=sftp_access.host,
#             port=sftp_access.port,
#         ),
#     )
#     ds = Dataset(
#         access_groups=["group1"],
#         contact_email="p.stibbons@uu.am",
#         creation_location="UU",
#         creation_time=datetime(2023, 6, 23, 10, 0, 0),
#         owner="PonderStibbons",
#         owner_group="uu",
#         principal_investigator="MustrumRidcully",
#         source_folder="/data",
#         type="raw",
#     )
#     ds.add_local_files(tmp_path / "file1.txt", base_path=tmp_path)
#     finalized = client.upload_new_dataset_now(ds)
#
#     downloaded = client.get_dataset(finalized.pid)
#     downloaded = client.download_files(downloaded, target=tmp_path / "download")
#
#     assert sftp_data_dir.joinpath("file1.txt").read_text() == "File contents"
#     assert downloaded.files[0].local_path.read_text() == "File contents"
