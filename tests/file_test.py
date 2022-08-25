# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from datetime import datetime, timezone

from pyscicat.model import DataFile
from scitacean import File


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


def test_file_with_model_from_local_file(fs):
    creation_time = (
        datetime.now()
        .astimezone(timezone.utc)
        .replace(microsecond=0, second=0, minute=0)
    )
    fs.create_file("./dir/events.nxs", st_size=9876)
    file = File.from_local("dir/events.nxs").with_model_from_local_file()
    assert str(file.source_path) == "events.nxs"
    assert file.source_folder is None
    assert file.remote_access_path is None
    assert str(file.local_path) == "dir/events.nxs"

    assert str(file.model.path) == "events.nxs"
    assert file.model.size == 9876

    # Ignoring seconds and minutes in order to be robust against latency in the test.
    t = datetime.fromisoformat(file.model.time).replace(second=0, minute=0)
    assert t == creation_time
