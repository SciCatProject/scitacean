# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from contextlib import contextmanager
from datetime import datetime, timedelta
from hashlib import md5
from typing import Dict

import dateutil.parser
from pyscicat.model import DataFile
import pytest
from scitacean import File
from scitacean.error import IntegrityError
from scitacean.file import checksum_of_file

from .common.files import make_file


@pytest.fixture
def fake_file(fs):
    return make_file(fs, path="local/dir/events.nxs")


def test_file_from_local(fake_file):
    file = File.from_local(fake_file["path"])

    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.checksum == fake_file["checksum"]
    assert file.size == fake_file["size"]

    assert file.model.path == str(fake_file["path"])
    assert file.model.size == fake_file["size"]
    assert file.model.chk == fake_file["checksum"]
    assert file.model.uid is None
    assert file.model.gid is None
    assert file.model.perm is None

    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)
    t = datetime.fromisoformat(file.model.time)
    assert abs(fake_file["creation_time"] - t) < timedelta(seconds=1)


def test_file_from_local_with_base_path(fake_file):
    file = File.from_local(fake_file["path"], base_path="local")

    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.checksum == fake_file["checksum"]
    assert file.size == fake_file["size"]

    assert file.model.path == "dir/events.nxs"
    assert file.model.size == fake_file["size"]
    assert file.model.chk == fake_file["checksum"]
    assert file.model.uid is None
    assert file.model.gid is None
    assert file.model.perm is None

    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)
    t = datetime.fromisoformat(file.model.time)
    assert abs(fake_file["creation_time"] - t) < timedelta(seconds=1)


def test_file_from_local_set_remote_path(fake_file):
    file = File.from_local(fake_file["path"], remote_path="remote/location/file.nxs")

    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.checksum == fake_file["checksum"]
    assert file.size == fake_file["size"]

    assert file.model.path == "remote/location/file.nxs"
    assert file.model.size == fake_file["size"]
    assert file.model.chk == fake_file["checksum"]
    assert file.model.uid is None
    assert file.model.gid is None
    assert file.model.perm is None

    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)
    t = datetime.fromisoformat(file.model.time)
    assert abs(fake_file["creation_time"] - t) < timedelta(seconds=1)


def test_file_from_local_set_source_folder(fake_file):
    file = File.from_local(fake_file["path"], source_folder="source")

    assert file.source_folder == "source"
    assert file.remote_access_path == "source/local/dir/events.nxs"
    assert file.local_path == fake_file["path"]
    assert file.checksum == fake_file["checksum"]
    assert file.size == fake_file["size"]

    assert file.model.path == "local/dir/events.nxs"
    assert file.model.size == fake_file["size"]
    assert file.model.chk == fake_file["checksum"]
    assert file.model.uid is None
    assert file.model.gid is None
    assert file.model.perm is None

    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)
    t = datetime.fromisoformat(file.model.time)
    assert abs(fake_file["creation_time"] - t) < timedelta(seconds=1)


def test_file_from_local_set_many_args(fake_file):
    file = File.from_local(
        fake_file["path"],
        base_path="local",
        source_folder="remote",
        remote_uid="user-usy",
        remote_gid="groupy-group",
        remote_perm="wrx",
    )

    assert file.source_folder == "remote"
    assert file.remote_access_path == "remote/dir/events.nxs"
    assert file.local_path == fake_file["path"]
    assert file.checksum == fake_file["checksum"]
    assert file.size == fake_file["size"]

    assert file.model.path == "dir/events.nxs"
    assert file.model.size == fake_file["size"]
    assert file.model.chk == fake_file["checksum"]
    assert file.model.uid == "user-usy"
    assert file.model.gid == "groupy-group"
    assert file.model.perm == "wrx"

    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)
    t = datetime.fromisoformat(file.model.time)
    assert abs(fake_file["creation_time"] - t) < timedelta(seconds=1)


@pytest.mark.parametrize("alg", ("md5", "sha256", "blake2s"))
def test_file_from_local_select_checksum_algorithm(fake_file, alg):
    file = File.from_local(fake_file["path"], checksum_algorithm=alg)
    expected = checksum_of_file(fake_file["path"], algorithm=alg)
    assert file.checksum == expected
    assert file.model.chk == expected


def test_file_from_scicat():
    model = DataFile(path="dir/image.jpg", size=12345, time="2022-06-22T15:42:53.123Z")
    file = File.from_scicat(model, source_folder="remote/source/folder")

    assert file.source_folder == "remote/source/folder"
    assert file.remote_access_path == "remote/source/folder/dir/image.jpg"
    assert file.local_path is None
    assert file.checksum is None
    assert file.size == 12345
    assert file.creation_time == dateutil.parser.parse("2022-06-22T15:42:53.123Z")

    assert file.model.path == "dir/image.jpg"
    assert file.model.size == 12345
    assert file.model.time == "2022-06-22T15:42:53.123Z"
    assert file.model.chk is None
    assert file.model.uid is None
    assert file.model.gid is None
    assert file.model.perm is None


class FakeDownloader:
    def __init__(self, files: Dict[str, bytes], fs):
        self.files = files
        self.fs = fs

    def download_file(self, *, remote, local):
        self.fs.create_file(local, contents=self.files[remote])

    @contextmanager
    def connect_for_download(self):
        yield self


def test_provide_locally_creates_local_file(fs):
    content = b"random-stuff"
    model = DataFile(
        path="folder/file.txt",
        size=len(content),
        time="2022-06-22T15:42:53+00:00",
        chk=md5(content).hexdigest(),
    )
    file = File.from_scicat(model, source_folder="remote/source/")
    downloader = FakeDownloader(files={"remote/source/folder/file.txt": content}, fs=fs)
    file.provide_locally("./local", downloader=downloader, checksum_algorithm="md5")

    with open("local/folder/file.txt", "rb") as f:
        assert f.read() == content


def test_provide_locally_ignores_checksum_if_alg_is_none(fs):
    content = b"random-stuff"
    # This is not a valid checksum, so it cannot be the checksum of the above.
    bad_checksum = "incorrect-checksum"
    model = DataFile(
        path="folder/file.txt",
        size=len(content),
        time="2022-06-22T15:42:53+00:00",
        chk=bad_checksum,
    )
    file = File.from_scicat(model, source_folder="remote/source/")
    downloader = FakeDownloader(files={"remote/source/folder/file.txt": content}, fs=fs)
    # Does not raise
    file.provide_locally("./local", downloader=downloader, checksum_algorithm=None)


def test_provide_locally_detects_bad_checksum(fs):
    content = b"random-stuff"
    # This is not a valid checksum, so it cannot be the checksum of the above.
    bad_checksum = "incorrect-checksum"
    model = DataFile(
        path="folder/file.txt",
        size=len(content),
        time="2022-06-22T15:42:53+00:00",
        chk=bad_checksum,
    )
    file = File.from_scicat(model, source_folder="remote/source/")
    downloader = FakeDownloader(files={"remote/source/folder/file.txt": content}, fs=fs)
    with pytest.raises(IntegrityError):
        file.provide_locally("./local", downloader=downloader, checksum_algorithm="md5")


def test_provide_locally_detects_bad_size_if_checksum_not_available(fs):
    content = b"random-stuff"
    model = DataFile(
        path="folder/file.txt", size=9999, time="2022-06-22T15:42:53+00:00"
    )
    file = File.from_scicat(model, source_folder="remote/source/")
    downloader = FakeDownloader(files={"remote/source/folder/file.txt": content}, fs=fs)
    with pytest.raises(IntegrityError):
        file.provide_locally("./local", downloader=downloader, checksum_algorithm=None)


def test_provide_locally_detects_bad_size_if_checksum_alg_is_none(fs):
    content = b"random-stuff"
    # This is not a valid checksum, so it cannot be the checksum of the above.
    bad_checksum = "incorrect-checksum"
    model = DataFile(
        path="folder/file.txt",
        size=9999,
        time="2022-06-22T15:42:53+00:00",
        chk=bad_checksum,
    )
    file = File.from_scicat(model, source_folder="remote/source/")
    downloader = FakeDownloader(files={"remote/source/folder/file.txt": content}, fs=fs)
    with pytest.raises(IntegrityError):
        file.provide_locally("./local", downloader=downloader, checksum_algorithm=None)
