# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
import os
from pathlib import Path
import re
from typing import Union

from dateutil.parser import parse as parse_date
import pytest
from scitacean.testing.transfer import FakeFileTransfer
from scitacean.model import DataFile, RawDataset, OrigDatablock
from scitacean import Client, Dataset, DatasetType, PID


@pytest.fixture
def data_files():
    contents = {
        "file1.dat": b"contents-of-file1",
        "log/what-happened.log": b"ERROR Flux is off the scale",
        "thaum.dat": b"0 4 2 59 330 2314552",
    }
    files = [
        DataFile(path=name, size=len(content)) for name, content in contents.items()
    ]
    return files, contents


@pytest.fixture
def dataset_and_files(data_files):
    model = RawDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=parse_date("1995-08-06T14:14:14"),
        owner="pstibbons",
        ownerGroup="faculty",
        pid=PID(prefix="UU.000", pid="5125.ab.663.8c9f"),
        principalInvestigator="m.ridcully@uu.am",
        sourceFolder="/src/stibbons/774",
        type=DatasetType.RAW,
    )
    block = OrigDatablock(
        ownerGroup="faculty",
        size=sum(f.size for f in data_files[0]),
        datasetId=PID(prefix="UU.000", pid="5125.ab.663.8c9f"),
        id=PID(prefix="UU.000", pid="0941.66.abff.41de"),
        dataFileList=data_files[0],
    )
    dset = Dataset.from_models(dataset_model=model, orig_datablock_models=[block])
    return dset, {
        os.path.join(dset.source_folder, name): content
        for name, content in data_files[1].items()
    }


def load(name: Union[str, Path]):
    with open(name, "rb") as f:
        return f.read()


def test_download_files_creates_local_files_select_all(fs, dataset_and_files):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=True)
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]
    assert (
        load("download/log/what-happened.log")
        == contents["/src/stibbons/774/log/what-happened.log"]
    )
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_none(fs, dataset_and_files):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=False)
    assert not Path("download/file1.dat").exists()
    assert not Path("download/log/what-happened.log").exists()
    assert not Path("download/thaum.dat").exists()


def test_download_files_creates_local_files_select_one_by_string(fs, dataset_and_files):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select="thaum.dat")
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]
    assert not Path("download/file1.dat").exists()
    assert not Path("download/log/what-happened.log").exists()


def test_download_files_creates_local_files_select_two_by_string(fs, dataset_and_files):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(
        dataset, target="./download", select=["thaum.dat", "log/what-happened.log"]
    )
    assert not Path("download/file1.dat").exists()
    assert (
        load("download/log/what-happened.log")
        == contents["/src/stibbons/774/log/what-happened.log"]
    )
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_one_by_regex_name_only(
    fs, dataset_and_files
):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=re.compile("thaum"))
    assert not Path("download/file1.dat").exists()
    assert not Path("download/log/what-happened.log").exists()
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_two_by_regex_suffix(
    fs, dataset_and_files
):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=re.compile(r"\.dat"))
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]
    assert not Path("download/log/what-happened.log").exists()
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_one_by_regex_full_path(
    fs, dataset_and_files
):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(
        dataset, target="./download", select=re.compile(r"^file1\.dat$")
    )
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]
    assert not Path("download/log/what-happened.log").exists()
    assert not Path("download/thaum.dat").exists()


def test_download_files_creates_local_files_select_one_by_predicate(
    fs, dataset_and_files
):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(
        dataset, target="./download", select=lambda f: f.remote_path == "file1.dat"
    )
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]
    assert not Path("download/log/what-happened.log").exists()
    assert not Path("download/thaum.dat").exists()
