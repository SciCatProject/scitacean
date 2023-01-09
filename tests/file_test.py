# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import hashlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from dateutil.parser import parse as parse_date

from scitacean import File, IntegrityError, RemotePath
from scitacean.file import checksum_of_file
from scitacean.logging import logger_name
from scitacean.model import DataFile

from .common.files import make_file


@pytest.fixture
def fake_file(fs):
    return make_file(fs, path="local/dir/events.nxs")


def test_file_from_local(fake_file):
    file = replace(File.from_local(fake_file["path"]), checksum_algorithm="md5")
    assert file.remote_access_path("/remote") is None
    assert file.local_path == fake_file["path"]
    assert file.remote_path == str(fake_file["path"])
    assert file.checksum() == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


def test_file_from_local_with_base_path(fake_file):
    assert str(fake_file["path"]) == "local/dir/events.nxs"  # used below

    file = replace(
        File.from_local(fake_file["path"], base_path="local"), checksum_algorithm="md5"
    )
    assert file.remote_access_path("/remote") is None
    assert file.local_path == fake_file["path"]
    assert file.remote_path == "dir/events.nxs"
    assert file.checksum() == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


def test_file_from_local_set_remote_path(fake_file):
    file = replace(
        File.from_local(fake_file["path"], remote_path="remote/location/file.nxs"),
        checksum_algorithm="md5",
    )
    assert file.remote_access_path("/remote") is None
    assert file.local_path == fake_file["path"]
    assert file.remote_path == "remote/location/file.nxs"
    assert file.checksum() == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


def test_file_from_local_set_many_args(fake_file):
    file = replace(
        File.from_local(
            fake_file["path"],
            base_path="local",
            remote_uid="user-usy",
            remote_gid="groupy-group",
            remote_perm="wrx",
        ),
        checksum_algorithm="md5",
    )
    assert file.remote_access_path("/remote") is None
    assert file.local_path == fake_file["path"]
    assert file.checksum() == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid == "user-usy"
    assert file.remote_gid == "groupy-group"
    assert file.remote_perm == "wrx"
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


@pytest.mark.parametrize("alg", ("md5", "sha256", "blake2s"))
def test_file_from_local_select_checksum_algorithm(fake_file, alg):
    file = replace(File.from_local(fake_file["path"]), checksum_algorithm=alg)
    expected = checksum_of_file(fake_file["path"], algorithm=alg)
    assert file.checksum() == expected


def test_file_from_scicat():
    model = DataFile(
        path="dir/image.jpg", size=12345, time=parse_date("2022-06-22T15:42:53.123Z")
    )
    file = File.from_scicat(model)

    assert file.remote_access_path("/remote/folder") == "/remote/folder/dir/image.jpg"
    assert file.local_path is None
    assert file.checksum() is None
    assert file.size == 12345
    assert file.creation_time == parse_date("2022-06-22T15:42:53.123Z")


def test_make_model_local_file(fake_file):
    file = replace(
        File.from_local(
            fake_file["path"],
            remote_uid="user-usy",
            remote_gid="groupy-group",
            remote_perm="wrx",
        ),
        checksum_algorithm="blake2s",
    )
    model = file.make_model()
    assert model.path == str(fake_file["path"])
    assert model.size == fake_file["size"]
    assert model.chk == checksum_of_file(fake_file["path"], algorithm="blake2s")
    assert model.gid == "groupy-group"
    assert model.perm == "wrx"
    assert model.uid == "user-usy"
    assert abs(fake_file["creation_time"] - model.time) < timedelta(seconds=1)


def test_uploaded(fake_file):
    file = replace(
        File.from_local(
            fake_file["path"],
            remote_uid="the-user",
        ),
        checksum_algorithm="sha256",
    )
    uploaded = file.uploaded(
        remote_gid="the-group", remote_creation_time=parse_date("2100-09-07T11:34:51")
    )

    assert uploaded.is_on_local
    assert uploaded.is_on_remote

    assert uploaded.remote_path == str(fake_file["path"])
    assert uploaded.local_path == fake_file["path"]
    assert uploaded.checksum() == checksum_of_file(
        fake_file["path"], algorithm="sha256"
    )
    assert uploaded.remote_uid == "the-user"
    assert uploaded.remote_gid == "the-group"
    assert uploaded._remote_creation_time == parse_date("2100-09-07T11:34:51")


def test_downloaded():
    model = DataFile(
        path="dir/stream.s",
        size=55123,
        time=parse_date("2025-01-09T21:00:21.421Z"),
        perm="xrw",
        createdBy="creator-id",
    )
    file = File.from_scicat(model)
    downloaded = file.downloaded(local_path="/local/stream.s")

    assert downloaded.is_on_local
    assert downloaded.is_on_remote

    assert downloaded.remote_path == RemotePath("dir/stream.s")
    assert downloaded.local_path == Path("/local/stream.s")
    assert downloaded.remote_perm == "xrw"
    assert downloaded.created_by == "creator-id"


def test_creation_time_is_always_local_time(fake_file):
    file = File.from_local(path=fake_file["path"])
    model = file.make_model()
    model.time = parse_date("2105-04-01T04:52:23")
    uploaded = file.uploaded()

    assert abs(fake_file["creation_time"] - uploaded.creation_time) < timedelta(
        seconds=1
    )


def test_size_is_always_local_size(fake_file):
    file = File.from_local(path=fake_file["path"])
    model = file.make_model()
    model.size = 999999999
    uploaded = file.uploaded()

    assert uploaded.size == fake_file["size"]


def test_checksum_is_always_local_checksum(fake_file):
    file = File.from_local(path=fake_file["path"])
    uploaded = replace(
        file.uploaded(), _remote_checksum="6e9eb73953231aebbbc8788f39f08618"
    )

    assert replace(uploaded, checksum_algorithm="md5").checksum() == checksum_of_file(
        fake_file["path"], algorithm="md5"
    )
    assert replace(
        uploaded, checksum_algorithm="sha256"
    ).checksum() == checksum_of_file(fake_file["path"], algorithm="sha256")


def test_creation_time_is_up_to_date(fs, fake_file):
    file = File.from_local(path=fake_file["path"])
    with open(fake_file["path"], "wb") as f:
        f.write(b"some new content to update time stamp")
    new_creation_time = datetime.fromtimestamp(
        fake_file["path"].stat().st_mtime
    ).astimezone(timezone.utc)
    assert file.creation_time == new_creation_time


def test_size_is_up_to_date(fs, fake_file):
    file = File.from_local(path=fake_file["path"])
    new_contents = b"content with a new size"
    assert len(new_contents) != fake_file["size"]
    with open(fake_file["path"], "wb") as f:
        f.write(new_contents)
    assert file.size == len(new_contents)


def test_checksum_is_up_to_date(fs, fake_file):
    file = replace(File.from_local(path=fake_file["path"]), checksum_algorithm="md5")
    new_contents = b"content a different checksum"

    checksum = hashlib.new("md5")
    checksum.update(new_contents)
    checksum = checksum.hexdigest()
    assert checksum != fake_file["size"]

    with open(fake_file["path"], "wb") as f:
        f.write(new_contents)
    assert file.checksum() == checksum


def test_validate_after_download_detects_bad_checksum(fake_file):
    model = DataFile(
        path=fake_file["path"].name,
        size=fake_file["size"],
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk="incorrect-checksum",
    )
    file = replace(
        File.from_scicat(model),
        checksum_algorithm="md5",
    )
    downloaded = file.downloaded(local_path=fake_file["path"])

    with pytest.raises(IntegrityError):
        downloaded.validate_after_download()


def test_validate_after_download_ignores_checksum_if_no_algorithm(fake_file):
    model = DataFile(
        path=fake_file["path"].name,
        size=fake_file["size"],
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk="incorrect-checksum",
    )
    file = File.from_scicat(model)
    downloaded = file.downloaded(local_path=fake_file["path"])

    # does not raise
    downloaded.validate_after_download()


def test_validate_after_download_detects_size_mismatch(fake_file, caplog):
    model = DataFile(
        path=fake_file["path"].name,
        size=fake_file["size"] + 100,
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk="incorrect-checksum",
    )
    file = replace(
        File.from_scicat(model),
        checksum_algorithm=None,
    )
    downloaded = file.downloaded(local_path=fake_file["path"])
    with caplog.at_level("INFO", logger=logger_name()):
        downloaded.validate_after_download()
    assert "does not match size reported in dataset" in caplog.text
