# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from datetime import timedelta

import pytest
from dateutil.parser import parse as parse_time

from scitacean import File
from scitacean.file import checksum_of_file
from scitacean.model import DataFile

from .common.files import make_file


@pytest.fixture
def fake_file(fs):
    return make_file(fs, path="local/dir/events.nxs")


def test_file_from_local(fake_file):
    file = File.from_local(fake_file["path"])
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.remote_path == str(fake_file["path"])
    assert file.checksum(algorithm="md5") == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


def test_file_from_local_with_base_path(fake_file):
    assert str(fake_file["path"]) == "local/dir/events.nxs"  # used below

    file = File.from_local(fake_file["path"], base_path="local")
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.remote_path == "dir/events.nxs"
    assert file.checksum(algorithm="md5") == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


def test_file_from_local_set_remote_path(fake_file):
    file = File.from_local(fake_file["path"], remote_path="remote/location/file.nxs")
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.remote_path == "remote/location/file.nxs"
    assert file.checksum(algorithm="md5") == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid is None
    assert file.remote_gid is None
    assert file.remote_perm is None
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


def test_file_from_local_cannot_set_source_folder(fake_file):
    with pytest.raises(TypeError):
        File.from_local(fake_file["path"], source_folder="source")  # noqa


def test_file_from_local_set_many_args(fake_file):
    file = File.from_local(
        fake_file["path"],
        base_path="local",
        remote_uid="user-usy",
        remote_gid="groupy-group",
        remote_perm="wrx",
    )
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert file.local_path == fake_file["path"]
    assert file.checksum(algorithm="md5") == fake_file["checksum"]
    assert file.size == fake_file["size"]
    assert file.remote_uid == "user-usy"
    assert file.remote_gid == "groupy-group"
    assert file.remote_perm == "wrx"
    assert abs(fake_file["creation_time"] - file.creation_time) < timedelta(seconds=1)


@pytest.mark.parametrize("alg", ("md5", "sha256", "blake2s"))
def test_file_from_local_select_checksum_algorithm(fake_file, alg):
    file = File.from_local(fake_file["path"])
    expected = checksum_of_file(fake_file["path"], algorithm=alg)
    assert file.checksum(algorithm=alg) == expected


def test_file_from_scicat():
    model = DataFile(
        path="dir/image.jpg", size=12345, time=parse_time("2022-06-22T15:42:53.123Z")
    )
    file = File.from_scicat(model, source_folder="remote/source/folder")

    assert file.source_folder == "remote/source/folder"
    assert file.remote_access_path == "remote/source/folder/dir/image.jpg"
    assert file.local_path is None
    assert file.checksum() is None
    assert file.size == 12345
    assert file.creation_time == parse_time("2022-06-22T15:42:53.123Z")


def test_make_model_local_file(fake_file):
    file = File.from_local(
        fake_file["path"],
        remote_uid="user-usy",
        remote_gid="groupy-group",
        remote_perm="wrx",
    )
    model = file.make_model(checksum_algorithm="blake2s")
    assert model.path == str(fake_file["path"])
    assert model.size == fake_file["size"]
    assert model.chk == checksum_of_file(fake_file["path"], algorithm="blake2s")
    assert model.gid == "groupy-group"
    assert model.perm == "wrx"
    assert model.uid == "user-usy"
    assert abs(fake_file["creation_time"] - model.time) < timedelta(seconds=1)


# TODO check that size, checklsum, creation_time are
#  - up to date if the file is only local
#  - always the stored value if file in on remote regardless whether on local

# TODO test downlaod validation
