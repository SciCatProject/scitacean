# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
from typing import Dict

from pyscicat.model import DataFile
import pytest
from scitacean import File
from scitacean.error import IntegrityError
from scitacean.file import checksum_of_file


@pytest.fixture
def fake_file(fs):
    contents = b"a bunch of file contents"
    checksum = hashlib.new("md5")
    checksum.update(contents)
    checksum = checksum.hexdigest()
    path = Path("./dir/events.nxs")
    fs.create_file(path, contents=contents)
    creation_time = datetime.now().astimezone(timezone.utc)
    return dict(
        path=path, creation_time=creation_time, checksum=checksum, size=len(contents)
    )


def test_file_from_local():
    file = File.from_local("local/dir/file.txt")
    assert str(file.source_path) == "file.txt"
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert str(file.local_path) == "local/dir/file.txt"
    assert file.model is None


def test_file_from_local_with_relative_to():
    file = File.from_local("local/dir/song.mp3", relative_to="remote/location")
    assert str(file.source_path) == "remote/location/song.mp3"
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert str(file.local_path) == "local/dir/song.mp3"
    assert file.model is None


def test_file_from_scicat():
    model = DataFile(path="dir/image.jpg", size=12345, time="2022-06-22T15:42:53+00:00")
    file = File.from_scicat(model, "remote/source/folder")
    assert str(file.source_path) == "dir/image.jpg"
    assert str(file.source_folder) == "remote/source/folder"
    assert str(file.remote_access_path) == "remote/source/folder/dir/image.jpg"
    assert file.local_path is None
    assert file.model == model


def test_file_with_model_from_local_file(fake_file):
    file = File.from_local(fake_file["path"]).with_model_from_local_file()
    assert file.source_path == Path(fake_file["path"].name)
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.checksum == fake_file["checksum"]

    assert file.model.path == fake_file["path"].name
    assert file.model.size == fake_file["size"]
    assert file.model.chk == fake_file["checksum"]

    t = datetime.fromisoformat(file.model.time)
    assert abs(fake_file["creation_time"] - t) < timedelta(seconds=1)


@pytest.mark.parametrize("alg", ("md5", "sha256", "blake2s"))
def test_file_with_model_from_local_file_can_select_checksum_algorithm(fake_file, alg):
    file = File.from_local(fake_file["path"]).with_model_from_local_file(
        checksum_algorithm=alg
    )
    expected = checksum_of_file(fake_file["path"], algorithm=alg)
    assert file.checksum == expected
    assert file.model.chk == expected


class FakeDownloader:
    def __init__(self, files: Dict[Path, bytes], fs):
        self.files = files
        self.fs = fs

    def get(self, *, remote, local):
        self.fs.create_file(local, contents=self.files[remote])


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
    file = File.from_scicat(model, "remote/source/")
    downloader = FakeDownloader(
        files={Path("remote/source/folder/file.txt"): content}, fs=fs
    )
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
    file = File.from_scicat(model, "remote/source/")
    downloader = FakeDownloader(
        files={Path("remote/source/folder/file.txt"): content}, fs=fs
    )
    with pytest.raises(IntegrityError):
        file.provide_locally("./local", downloader=downloader, checksum_algorithm="md5")


def test_provide_locally_detects_bad_size_if_checksum_not_available(fs):
    content = b"random-stuff"
    model = DataFile(
        path="folder/file.txt", size=9999, time="2022-06-22T15:42:53+00:00"
    )
    file = File.from_scicat(model, "remote/source/")
    downloader = FakeDownloader(
        files={Path("remote/source/folder/file.txt"): content}, fs=fs
    )
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
    file = File.from_scicat(model, "remote/source/")
    downloader = FakeDownloader(
        files={Path("remote/source/folder/file.txt"): content}, fs=fs
    )
    with pytest.raises(IntegrityError):
        file.provide_locally("./local", downloader=downloader, checksum_algorithm=None)
