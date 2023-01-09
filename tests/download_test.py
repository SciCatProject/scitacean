# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import hashlib
import re
from pathlib import Path
from typing import Union

import pytest
from dateutil.parser import parse as parse_date

from scitacean import PID, Client, Dataset, DatasetType, File, IntegrityError
from scitacean.filesystem import RemotePath
from scitacean.logging import logger_name
from scitacean.model import DataFile, OrigDatablock, RawDataset
from scitacean.testing.transfer import FakeFileTransfer


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
        sourceFolder=RemotePath("/src/stibbons/774"),
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
        dset.source_folder / name: content for name, content in data_files[1].items()
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


def test_download_files_returns_updated_dataset(fs, dataset_and_files):
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    finalized = client.download_files(dataset, target="./download")

    for f in finalized.files:
        assert f.is_on_local
    for f in dataset.files:
        assert not f.is_on_local  # original is unchanged


def test_download_files_ignores_checksum_if_alg_is_none(fs, dataset_and_files):
    dataset, contents = dataset_and_files

    content = b"random-stuff"
    bad_checksum = "incorrect-checksum"
    model = DataFile(
        path="file.txt",
        size=len(content),
        time=parse_date("2022-06-22T15:42:53+00:00"),
        chk=bad_checksum,
    )
    dataset.add_orig_datablock(checksum_algorithm=None)
    dataset.add_files(File.from_scicat(model))

    client = Client.without_login(
        url="/",
        file_transfer=FakeFileTransfer(
            fs=fs, files={dataset.source_folder / "file.txt": content}
        ),
    )
    # Does not raise
    client.download_files(dataset, target="./download", select="file.txt")


def test_download_files_detects_bad_checksum(fs, dataset_and_files):
    dataset, contents = dataset_and_files

    content = b"random-stuff"
    bad_checksum = "incorrect-checksum"
    model = DataFile(
        path="file.txt",
        size=len(content),
        time=parse_date("2022-06-22T15:42:53+00:00"),
        chk=bad_checksum,
    )
    dataset.add_orig_datablock(checksum_algorithm="md5")
    dataset.add_files(File.from_scicat(model))

    client = Client.without_login(
        url="/",
        file_transfer=FakeFileTransfer(
            fs=fs, files={dataset.source_folder / "file.txt": content}
        ),
    )
    with pytest.raises(IntegrityError):
        client.download_files(dataset, target="./download", select="file.txt")


def test_download_files_detects_bad_size(fs, dataset_and_files, caplog):
    dataset, contents = dataset_and_files

    content = b"random-stuff"
    bad_checksum = hashlib.md5(content).hexdigest()
    model = DataFile(
        path="file.txt",
        size=89412,  # Too large
        time=parse_date("2022-06-22T15:42:53+00:00"),
        chk=bad_checksum,
    )
    dataset.add_orig_datablock(checksum_algorithm="md5")
    dataset.add_files(File.from_scicat(model))

    client = Client.without_login(
        url="/",
        file_transfer=FakeFileTransfer(
            fs=fs, files={dataset.source_folder / "file.txt": content}
        ),
    )
    with caplog.at_level("INFO", logger=logger_name()):
        client.download_files(dataset, target="./download", select="file.txt")
    assert "does not match size reported in dataset" in caplog.text
    assert "89412" in caplog.text
