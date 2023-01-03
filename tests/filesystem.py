# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scitacean.filesystem import (
    RemotePath,
    checksum_of_file,
    file_modification_time,
    file_size,
)


def test_remote_path_creation_and_str():
    assert str(RemotePath("/mnt/data/folder/file.txt")) == "/mnt/data/folder/file.txt"
    assert str(RemotePath("dir/image.png")) == "dir/image.png"
    assert str(RemotePath("data.nxs")) == "data.nxs"
    assert str(RemotePath(RemotePath("source/events.h5"))) == "source/events.h5"


def test_remote_path_init_requires_path_like():
    with pytest.raises(TypeError):
        RemotePath(6133)  # type: ignore
    with pytest.raises(TypeError):
        RemotePath(["folder", "file.dat"])  # type: ignore


@pytest.mark.parametrize(
    "types", ((RemotePath, RemotePath), (RemotePath, str), (str, RemotePath))
)
def test_remote_path_eq(types):
    ta, tb = types
    assert ta("/source/data.csv") == tb("/source/data.csv")


@pytest.mark.parametrize(
    "types", ((RemotePath, RemotePath), (RemotePath, str), (str, RemotePath))
)
def test_remote_path_neq(types):
    ta, tb = types
    assert ta("/source/data.csv") != tb("/host/dir/song.mp3")


@pytest.mark.parametrize(
    "types", ((RemotePath, RemotePath), (RemotePath, str), (str, RemotePath))
)
def test_remote_path_join(types):
    ta, tb = types
    assert ta("/source/123") / tb("file.data") == RemotePath("/source/123/file.data")
    assert ta("/source/123/") / tb("file.data") == RemotePath("/source/123/file.data")
    assert ta("/source/123") / tb("/file.data") == RemotePath("/source/123/file.data")
    assert ta("/source/123/") / tb("/file.data") == RemotePath("/source/123/file.data")


@pytest.mark.parametrize(
    "types", ((RemotePath, RemotePath), (RemotePath, str), (str, RemotePath))
)
def test_remote_path_join_url(types):
    ta, tb = types
    assert ta("https://server.eu") / tb("1234-abcd/data.txt") == RemotePath(
        "https://server.eu/1234-abcd/data.txt"
    )
    assert ta("https://server.eu/") / tb("1234-abcd/data.txt") == RemotePath(
        "https://server.eu/1234-abcd/data.txt"
    )
    assert ta("https://server.eu") / tb("/1234-abcd/data.txt") == RemotePath(
        "https://server.eu/1234-abcd/data.txt"
    )
    assert ta("https://server.eu/") / tb("/1234-abcd/data.txt") == RemotePath(
        "https://server.eu/1234-abcd/data.txt"
    )


def test_remote_path_name():
    assert RemotePath("table.csv").name == "table.csv"
    assert RemotePath("README").name == "README"
    assert RemotePath("path/").name == "path"
    assert RemotePath("dir/folder/file1.txt").name == "file1.txt"


def test_remote_path_suffix():
    assert RemotePath("file.txt").suffix == ".txt"
    assert RemotePath("folder/image.png").suffix == ".png"
    assert RemotePath("dir/table.txt.csv").suffix == ".csv"
    assert RemotePath("archive.tz/data.dat").suffix == ".dat"
    assert RemotePath("location.dir/file").suffix is None
    assert RemotePath("source/file").suffix is None


@pytest.mark.parametrize("size", (0, 1, 57121))
def test_file_size(fs, size):
    fs.create_file("image.tiff", st_size=size)
    assert file_size(Path("image.tiff")) == size


def test_file_modification_time(fs):
    fs.create_file("data.dat")
    expected = datetime.now(tz=timezone.utc)
    assert abs(file_modification_time(Path("data.dat")) - expected) < timedelta(
        seconds=5
    )


@pytest.mark.parametrize(
    "contents",
    (b"small file contents", b"large contents " * 100000),
    ids=("small", "large"),
)
def test_checksum_of_file(fs, contents):
    fs.create_file("file.txt", contents=contents)

    assert (
        checksum_of_file("file.txt", algorithm="md5")
        == hashlib.md5(contents).hexdigest()
    )
    assert (
        checksum_of_file("file.txt", algorithm="sha256")
        == hashlib.sha256(contents).hexdigest()
    )
