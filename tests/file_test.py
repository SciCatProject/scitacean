# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
import hashlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from dateutil.parser import parse as parse_date
from pyfakefs.fake_filesystem import FakeFilesystem

from scitacean import File, IntegrityError, RemotePath
from scitacean.filesystem import checksum_of_file
from scitacean.logging import logger_name
from scitacean.model import DownloadDataFile

from .common.files import make_file


@pytest.fixture
def fake_file(fs: FakeFilesystem) -> dict[str, Any]:
    return make_file(fs, path=Path("local", "dir", "events.nxs"))


def test_file_from_local(fake_file: dict[str, Any]) -> None:
    file = replace(File.from_local(fake_file["path"]), checksum_algorithm="md5")
    assert file.remote_access_path("/remote") is None
    assert file.local_path == fake_file["path"]
    assert file.remote_path == fake_file["path"].as_posix()
    assert file.checksum() == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


def test_file_from_local_with_base_path(fake_file: dict[str, Any]) -> None:
    assert fake_file["path"] == Path("local", "dir", "events.nxs")  # used below

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


def test_file_from_local_set_remote_path(fake_file: dict[str, Any]) -> None:
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


def test_file_from_local_set_many_args(fake_file: dict[str, Any]) -> None:
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


@pytest.mark.parametrize("alg", ["md5", "sha256", "blake2s"])
def test_file_from_local_select_checksum_algorithm(
    fake_file: dict[str, Any], alg: str
) -> None:
    file = replace(File.from_local(fake_file["path"]), checksum_algorithm=alg)
    expected = checksum_of_file(fake_file["path"], algorithm=alg)
    assert file.checksum() == expected


def test_file_from_local_remote_path_uses_forward_slash(fs: FakeFilesystem) -> None:
    fs.create_file(Path("data", "subdir", "file.dat"))

    file = File.from_local(Path("data", "subdir", "file.dat"))
    assert file.remote_path == RemotePath("data/subdir/file.dat")
    assert file.make_model().path == "data/subdir/file.dat"

    file = File.from_local(Path("data", "subdir", "file.dat"), base_path=Path("data"))
    assert file.remote_path == RemotePath("subdir/file.dat")
    assert file.make_model().path == "subdir/file.dat"

    file = File.from_local(
        Path("data", "subdir", "file.dat"), base_path=Path("data") / "subdir"
    )
    assert file.remote_path == RemotePath("file.dat")
    assert file.make_model().path == "file.dat"


def test_file_from_remote_default_args() -> None:
    file = File.from_remote(
        remote_path="/remote/source/file.nxs",
        size=6123,
        creation_time="2023-09-27T16:00:15Z",
    )
    assert file.local_path is None
    assert isinstance(file.remote_path, RemotePath)
    assert file.remote_path == "/remote/source/file.nxs"
    assert file.size == 6123
    assert isinstance(file.creation_time, datetime)
    assert file.creation_time == parse_date("2023-09-27T16:00:15Z")
    assert file.checksum() is None
    assert file.checksum_algorithm is None
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None


def test_file_from_remote_all_args() -> None:
    file = File.from_remote(
        remote_path="/remote/image.png",
        size=9,
        creation_time=parse_date("2023-10-09T08:12:59Z"),
        checksum="abcde",
        checksum_algorithm="md5",
        remote_uid="user-usy",
        remote_gid="groupy-group",
        remote_perm="wrx",
    )
    assert file.local_path is None
    assert file.remote_path == "/remote/image.png"
    assert file.size == 9
    assert file.creation_time == parse_date("2023-10-09T08:12:59Z")
    assert file.checksum() == "abcde"
    assert file.checksum_algorithm == "md5"
    assert file.remote_uid == "user-usy"
    assert file.remote_gid == "groupy-group"
    assert file.remote_perm == "wrx"


def test_file_from_remote_checksum_requires_algorithm() -> None:
    with pytest.raises(TypeError, match="checksum"):
        File.from_remote(
            remote_path="/remote/image.png",
            size=9,
            creation_time="2023-10-09T08:12:59Z",
            checksum="abcde",
        )


def test_file_from_download_model() -> None:
    model = DownloadDataFile(
        path="dir/image.jpg", size=12345, time=parse_date("2022-06-22T15:42:53.123Z")
    )
    file = File.from_download_model(model)

    assert file.remote_access_path("/remote/folder") == "/remote/folder/dir/image.jpg"
    assert file.local_path is None
    assert file.checksum() is None
    assert file.size == 12345
    assert file.creation_time == parse_date("2022-06-22T15:42:53.123Z")


def test_file_from_download_model_remote_path_uses_forward_slash() -> None:
    file = File.from_download_model(
        DownloadDataFile(
            path="data/subdir/file.dat",
            size=0,
            time=parse_date("2022-06-22T15:42:53.123Z"),
        ),
        local_path=None,
    )
    assert file.remote_path == RemotePath("data/subdir/file.dat")

    file = File.from_download_model(
        DownloadDataFile(
            path="data/subdir/file.dat",
            size=0,
            time=parse_date("2022-06-22T15:42:53.123Z"),
        ),
        local_path=Path("data") / "subdir",
    )
    assert file.remote_path == RemotePath("data/subdir/file.dat")


def test_make_model_local_file(fake_file: dict[str, Any]) -> None:
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
    assert model.path == fake_file["path"].as_posix()
    assert model.size == fake_file["size"]
    assert model.chk == checksum_of_file(fake_file["path"], algorithm="blake2s")
    assert model.gid == "groupy-group"
    assert model.perm == "wrx"
    assert model.uid == "user-usy"
    assert abs(fake_file["creation_time"] - model.time) < timedelta(seconds=1)


def test_uploaded(fake_file: dict[str, Any]) -> None:
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

    assert uploaded.remote_path == fake_file["path"].as_posix()
    assert uploaded.local_path == fake_file["path"]
    assert uploaded.checksum() == checksum_of_file(
        fake_file["path"], algorithm="sha256"
    )
    assert uploaded.remote_uid == "the-user"
    assert uploaded.remote_gid == "the-group"
    assert uploaded._remote_creation_time == parse_date("2100-09-07T11:34:51")


def test_downloaded() -> None:
    model = DownloadDataFile(
        path="dir/stream.s",
        size=55123,
        time=parse_date("2025-01-09T21:00:21.421Z"),
        perm="xrw",
    )
    file = File.from_download_model(model)
    downloaded = file.downloaded(local_path="/local/stream.s")

    assert downloaded.is_on_local
    assert downloaded.is_on_remote

    assert downloaded.remote_path == RemotePath("dir/stream.s")
    assert downloaded.local_path == Path("/local/stream.s")
    assert downloaded.remote_perm == "xrw"


def test_creation_time_is_always_local_time(fake_file: dict[str, Any]) -> None:
    file = File.from_local(path=fake_file["path"])
    model = file.make_model()
    model.time = parse_date("2105-04-01T04:52:23")
    uploaded = file.uploaded()

    assert abs(fake_file["creation_time"] - uploaded.creation_time) < timedelta(
        seconds=1
    )


def test_size_is_always_local_size(fake_file: dict[str, Any]) -> None:
    file = File.from_local(path=fake_file["path"])
    model = file.make_model()
    model.size = 999999999
    uploaded = file.uploaded()

    assert uploaded.size == fake_file["size"]


def test_checksum_is_always_local_checksum(fake_file: dict[str, Any]) -> None:
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


def test_creation_time_is_up_to_date(
    fs: FakeFilesystem, fake_file: dict[str, Any]
) -> None:
    file = File.from_local(path=fake_file["path"])
    with open(fake_file["path"], "wb") as f:
        f.write(b"some new content to update time stamp")
    new_creation_time = datetime.fromtimestamp(
        fake_file["path"].stat().st_mtime
    ).astimezone(timezone.utc)
    assert file.creation_time == new_creation_time


def test_size_is_up_to_date(fs: FakeFilesystem, fake_file: dict[str, Any]) -> None:
    file = File.from_local(path=fake_file["path"])
    new_contents = b"content with a new size"
    assert len(new_contents) != fake_file["size"]
    with open(fake_file["path"], "wb") as f:
        f.write(new_contents)
    assert file.size == len(new_contents)


def test_checksum_is_up_to_date(fs: FakeFilesystem, fake_file: dict[str, Any]) -> None:
    file = replace(File.from_local(path=fake_file["path"]), checksum_algorithm="md5")
    new_contents = b"content a different checksum"

    checksum = hashlib.new("md5")
    checksum.update(new_contents)
    checksum_digest = checksum.hexdigest()
    assert checksum_digest != fake_file["size"]

    with open(fake_file["path"], "wb") as f:
        f.write(new_contents)
    assert file.checksum() == checksum_digest


def test_validate_after_download_detects_bad_checksum(
    fake_file: dict[str, Any],
) -> None:
    model = DownloadDataFile(
        path=fake_file["path"].name,
        size=fake_file["size"],
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk="incorrect-checksum",
    )
    file = replace(
        File.from_download_model(model),
        checksum_algorithm="md5",
    )
    downloaded = file.downloaded(local_path=fake_file["path"])

    with pytest.raises(IntegrityError):
        downloaded.validate_after_download()


def test_validate_after_download_ignores_checksum_if_no_algorithm(
    fake_file: dict[str, Any],
) -> None:
    model = DownloadDataFile(
        path=fake_file["path"].name,
        size=fake_file["size"],
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk="incorrect-checksum",
    )
    file = File.from_download_model(model)
    downloaded = file.downloaded(local_path=fake_file["path"])

    # does not raise
    downloaded.validate_after_download()


def test_validate_after_download_detects_size_mismatch(
    fake_file: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    model = DownloadDataFile(
        path=fake_file["path"].name,
        size=fake_file["size"] + 100,
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk="incorrect-checksum",
    )
    file = replace(
        File.from_download_model(model),
        checksum_algorithm=None,
    )
    downloaded = file.downloaded(local_path=fake_file["path"])
    with caplog.at_level("INFO", logger=logger_name()):
        downloaded.validate_after_download()
    assert "does not match size reported in dataset" in caplog.text


@pytest.mark.parametrize("chk", ["sha256", None])
def test_local_is_not_up_to_date_for_remote_file(chk: str | None) -> None:
    file = File.from_download_model(
        DownloadDataFile(
            path="data.csv",
            size=65178,
            chk=chk,
            time=parse_date("2022-06-22T15:42:53.123Z"),
        )
    )
    assert not file.local_is_up_to_date()


def test_local_is_up_to_date_for_local_file() -> None:
    # Note that the file does not actually exist on disk but the test still works.
    file = File.from_local(path="image.jpg")
    assert file.local_is_up_to_date()


def test_local_is_up_to_date_default_checksum_alg(fs: FakeFilesystem) -> None:
    contents = b"some file content"
    checksum = hashlib.new("blake2b")
    checksum.update(contents)
    checksum_digest = checksum.hexdigest()
    fs.create_file("data.csv", contents=contents)

    file = File.from_download_model(
        DownloadDataFile(
            path="data.csv",
            size=65178,
            chk=checksum_digest,
            time=parse_date("2022-06-22T15:42:53.123Z"),
        )
    ).downloaded(local_path="data.csv")
    with pytest.warns(UserWarning):
        assert file.local_is_up_to_date()


def test_local_is_up_to_date_matching_checksum(fake_file: dict[str, Any]) -> None:
    model = DownloadDataFile(
        path=fake_file["path"].name,
        size=fake_file["size"],
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk=fake_file["checksum"],
    )
    file = replace(
        File.from_download_model(model).downloaded(local_path=fake_file["path"]),
        checksum_algorithm="md5",
    )
    assert file.local_is_up_to_date()


def test_local_is_not_up_to_date_differing_checksum(fake_file: dict[str, Any]) -> None:
    model = DownloadDataFile(
        path=fake_file["path"].name,
        size=fake_file["size"],
        time=parse_date("2022-06-22T15:42:53.123Z"),
        chk="a-different-checksum",
    )
    file = replace(
        File.from_download_model(model).downloaded(local_path=fake_file["path"]),
        checksum_algorithm="md5",
    )
    assert not file.local_is_up_to_date()
