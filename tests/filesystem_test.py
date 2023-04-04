# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath

import pytest
from hypothesis import given
from hypothesis import strategies as st

from scitacean.filesystem import (
    RemotePath,
    checksum_of_file,
    escape_path,
    file_modification_time,
    file_size,
)


def test_remote_path_creation_and_posix():
    assert RemotePath("/mnt/data/folder/file.txt").posix == "/mnt/data/folder/file.txt"
    assert RemotePath("dir/image.png").posix == "dir/image.png"
    assert RemotePath("data.nxs").posix == "data.nxs"
    assert RemotePath(RemotePath("source/events.h5")).posix == "source/events.h5"


def test_remote_path_from_segments():
    assert RemotePath("/mnt", "dir", "file.csv") == RemotePath("/mnt/dir/file.csv")
    assert RemotePath("folder", "file") == RemotePath("folder/file")
    assert RemotePath("", "folder", "file.csv") == RemotePath("folder/file.csv")
    assert RemotePath("folder", "", "file.csv") == RemotePath("folder/file.csv")
    assert RemotePath("folder", "file.csv", "") == RemotePath("folder/file.csv")


def test_remote_path_init_requires_path_like():
    with pytest.raises(TypeError):
        RemotePath(6133)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        RemotePath(["folder", "file.dat"])  # type: ignore[arg-type]


@pytest.mark.parametrize("local_type", (PurePath, Path))
def test_remote_path_rejects_os_path(local_type):
    with pytest.raises(TypeError):
        RemotePath(local_type("dir", "file.csv"))  # type: ignore[arg-type]


@pytest.mark.parametrize("local_type", (PurePath, PurePosixPath, PureWindowsPath))
def test_remote_path_from_local(local_type):
    local_path = local_type("dir", "folder", "file.csv")
    remote_path = RemotePath.from_local(local_path)
    assert remote_path == RemotePath("dir/folder/file.csv")


@pytest.mark.parametrize("local_type", (PurePath, PurePosixPath, PureWindowsPath))
def test_remote_path_posix_uses_forward_slashes(local_type):
    local_path = local_type("dir", "folder", "file.csv")
    remote_path = RemotePath.from_local(local_path)
    assert remote_path.posix == "dir/folder/file.csv"


def test_remote_path_str():
    assert str(RemotePath("folder/file.dat")) == "RemotePath('folder/file.dat')"


def test_remote_path_repr():
    assert repr(RemotePath("folder/file.dat")) == "RemotePath('folder/file.dat')"


def test_remote_path_to_local():
    assert RemotePath("folder/file.dat").to_local() == PurePath("folder", "file.dat")
    assert RemotePath("/folder/file.dat").to_local() == PurePath("/folder", "file.dat")
    assert RemotePath("folder//file.dat").to_local() == PurePath("folder", "file.dat")
    assert RemotePath("folder/file.dat/").to_local() == PurePath("folder", "file.dat")


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


def test_remote_path_join_rejects_os_path():
    with pytest.raises(TypeError):
        RemotePath("asd") / Path("qwe")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Path("qwe") / RemotePath("asd")  # type: ignore[arg-type]


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


def test_remote_path_truncated():
    assert RemotePath("something-long.txt").truncated(10) == "someth.txt"
    assert RemotePath("longlonglong/short").truncated(5) == "longl/short"
    assert RemotePath("a-long.data.dir/filename.csv").truncated(7) == "a-l.dir/fil.csv"
    assert RemotePath("file.longextension").truncated(9) == "f.longext"


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


@pytest.mark.parametrize("path_type", (str, Path, RemotePath))
def test_escape_path_returns_same_type_as_input(path_type):
    assert isinstance(escape_path(path_type("x")), path_type)


@given(st.text())
def test_escape_path_returns_ascii(path):
    # does not raise
    escape_path(path).encode("ascii", "strict")


@given(st.text())
def test_escape_path_returns_no_bad_character(path):
    bad_linux = "/" + chr(0)
    bad_windows = '<>:"\\/|?*' + "".join(map(chr, range(0, 31)))
    escaped = escape_path(path)
    assert not any(c in escaped for c in bad_linux + bad_windows)
