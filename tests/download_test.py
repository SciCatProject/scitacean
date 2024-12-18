# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
import hashlib
import re
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import pytest
from dateutil.parser import parse as parse_date
from pyfakefs.fake_filesystem import FakeFilesystem

from scitacean import PID, Client, Dataset, DatasetType, File, IntegrityError
from scitacean.filesystem import RemotePath
from scitacean.logging import logger_name
from scitacean.model import DownloadDataFile, DownloadDataset, DownloadOrigDatablock
from scitacean.testing.transfer import FakeDownloadConnection, FakeFileTransfer


def _checksum(data: bytes) -> str:
    checksum = hashlib.new("md5")
    checksum.update(data)
    return checksum.hexdigest()


@pytest.fixture
def data_files() -> tuple[list[DownloadDataFile], dict[str, bytes]]:
    contents = {
        "file1.dat": b"contents-of-file1",
        "log/what-happened.log": b"ERROR Flux is off the scale",
        "/src/stibbons/774/thaum.dat": b"0 4 2 59 330 2314552",
        "/src/ridcully/grades.csv": b"3,12,-2",
    }
    files = [
        DownloadDataFile(
            path=name,
            size=len(content),
            chk=_checksum(content),
            time=parse_date("1995-08-06T14:14:14"),
        )
        for name, content in contents.items()
    ]
    return files, contents


DatasetAndFiles = tuple[Dataset, dict[str, bytes]]


@pytest.fixture
def dataset_and_files(
    data_files: tuple[list[DownloadDataFile], dict[str, bytes]],
) -> DatasetAndFiles:
    model = DownloadDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=parse_date("1995-08-06T14:14:14"),
        numberOfFiles=len(data_files[0]),
        numberOfFilesArchived=0,
        owner="pstibbons",
        ownerGroup="faculty",
        packedSize=0,
        pid=PID(prefix="UU.000", pid="5125.ab.663.8c9f"),
        principalInvestigator="m.ridcully@uu.am",
        size=sum(f.size for f in data_files[0]),  # type: ignore[misc]
        sourceFolder=RemotePath("/src/stibbons/774"),
        type=DatasetType.RAW,
        scientificMetadata={
            "height": {"value": 0.3, "unit": "m"},
            "mass": "hefty",
        },
    )
    block = DownloadOrigDatablock(
        chkAlg="md5",
        ownerGroup="faculty",
        size=sum(f.size for f in data_files[0]),  # type: ignore[misc]
        datasetId=PID(prefix="UU.000", pid="5125.ab.663.8c9f"),
        _id="0941.66.abff.41de",
        dataFileList=data_files[0],
    )
    dset = Dataset.from_download_models(
        dataset_model=model, orig_datablock_models=[block]
    )

    content_abs_path = {
        file_absolute_path(name, dset.source_folder): content
        for name, content in data_files[1].items()
    }
    return dset, content_abs_path


def file_absolute_path(path: str, source_folder: RemotePath | None) -> str:
    if path.startswith("/"):
        return path
    return (source_folder / path).posix  # type: ignore[operator]


def load(name: str | Path) -> bytes:
    with open(name, "rb") as f:
        return f.read()


def test_download_files_creates_local_files_select_all(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=True)
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]
    assert (
        load("download/what-happened.log")
        == contents["/src/stibbons/774/log/what-happened.log"]
    )
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]
    assert load("download/grades.csv") == contents["/src/ridcully/grades.csv"]


def test_download_files_creates_local_files_select_none(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=False)
    assert not list(Path("download").iterdir())


def test_download_files_creates_local_files_select_one_by_string(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(
        dataset, target="./download", select="/src/stibbons/774/thaum.dat"
    )
    assert len(list(Path("download").iterdir())) == 1
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_two_by_string(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(
        dataset,
        target="./download",
        select=["/src/stibbons/774/thaum.dat", "log/what-happened.log"],
    )
    assert len(list(Path("download").iterdir())) == 2
    assert (
        load("download/what-happened.log")
        == contents["/src/stibbons/774/log/what-happened.log"]
    )
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_one_by_regex_name_only(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=re.compile("thaum"))
    assert len(list(Path("download").iterdir())) == 1
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_two_by_regex_suffix(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=re.compile(r"\.dat"))
    assert len(list(Path("download").iterdir())) == 2
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]
    assert load("download/thaum.dat") == contents["/src/stibbons/774/thaum.dat"]


def test_download_files_creates_local_files_select_one_by_regex_full_path(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(
        dataset, target="./download", select=re.compile(r"^file1\.dat$")
    )
    assert len(list(Path("download").iterdir())) == 1
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]


def test_download_files_creates_local_files_select_one_by_predicate(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(
        dataset, target="./download", select=lambda f: f.remote_path == "file1.dat"
    )
    assert len(list(Path("download").iterdir())) == 1
    assert load("download/file1.dat") == contents["/src/stibbons/774/file1.dat"]


def test_download_files_refuses_download_if_flattening_creates_clash(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    contents["sub_directory/file1.dat"] = b"second file with the same name"
    dataset.add_files(
        File.from_remote(
            "sub_directory/file1.dat",
            size=len(contents["sub_directory/file1.dat"]),
            creation_time=parse_date("1995-08-06T14:14:14"),
            checksum=_checksum(contents["sub_directory/file1.dat"]),
            checksum_algorithm="md5",
        )
    )
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    with pytest.raises(RuntimeError, match="file1.dat"):
        client.download_files(dataset, target="./download", select=True)
    assert not list(Path("download").iterdir())


def test_download_files_returns_updated_dataset(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files
    original = deepcopy(dataset)
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    finalized = client.download_files(dataset, target="./download")

    assert dataset == original
    assert all(
        getattr(finalized, field.name) == getattr(original, field.name)
        for field in original.fields()
    )
    assert finalized.meta == original.meta
    for f in finalized.files:
        assert f.is_on_local
    for f in dataset.files:
        assert not f.is_on_local  # original is unchanged


def test_download_files_ignores_checksum_if_alg_is_none(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files

    content = b"random-stuff"
    bad_checksum = "incorrect-checksum"
    model = DownloadDataFile(
        path="file.txt",
        size=len(content),
        time=parse_date("2022-06-22T15:42:53+00:00"),
        chk=bad_checksum,
    )
    dataset.add_orig_datablock(checksum_algorithm=None)
    dataset.add_files(File.from_download_model(model))
    assert dataset.source_folder is not None

    client = Client.without_login(
        url="/",
        file_transfer=FakeFileTransfer(
            fs=fs, files={dataset.source_folder / "file.txt": content}
        ),
    )
    # Does not raise
    client.download_files(dataset, target="./download", select="file.txt")


def test_download_files_detects_bad_checksum(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    dataset, contents = dataset_and_files

    content = b"random-stuff"
    bad_checksum = "incorrect-checksum"
    model = DownloadDataFile(
        path="file.txt",
        size=len(content),
        time=parse_date("2022-06-22T15:42:53+00:00"),
        chk=bad_checksum,
    )
    dataset.add_orig_datablock(checksum_algorithm="md5")
    dataset.add_files(File.from_download_model(model))
    assert dataset.source_folder is not None

    client = Client.without_login(
        url="/",
        file_transfer=FakeFileTransfer(
            fs=fs, files={dataset.source_folder / "file.txt": content}
        ),
    )
    with pytest.raises(IntegrityError):
        client.download_files(dataset, target="./download", select="file.txt")


def test_download_files_detects_bad_size(
    fs: FakeFilesystem,
    dataset_and_files: DatasetAndFiles,
    caplog: pytest.LogCaptureFixture,
) -> None:
    dataset, contents = dataset_and_files

    content = b"random-stuff"
    bad_checksum = hashlib.md5(content).hexdigest()
    model = DownloadDataFile(
        path="file.txt",
        size=89412,  # Too large
        time=parse_date("2022-06-22T15:42:53+00:00"),
        chk=bad_checksum,
    )
    dataset.add_orig_datablock(checksum_algorithm="md5")
    dataset.add_files(File.from_download_model(model))
    assert dataset.source_folder is not None

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


def test_download_does_not_download_up_to_date_file(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    # Ensure the file exists locally
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=True)

    # Downloading the same files again should not call the downloader.
    class RaisingDownloader(FakeFileTransfer):
        source_dir = "/"

        @contextmanager
        def connect_for_download(self) -> Iterator[FakeDownloadConnection]:
            raise RuntimeError("Download disabled")

    client = Client.without_login(
        url="/",
        file_transfer=RaisingDownloader(fs=fs),
    )
    # Does not raise
    downloaded = client.download_files(dataset, target="./download", select=True)
    assert all(file.local_path is not None for file in downloaded.files)


def test_download_does_not_download_up_to_date_file_manual_checksum(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    # Ensure the file exists locally
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=True)

    # Downloading the same files again should not call the downloader.
    class RaisingDownloader(FakeFileTransfer):
        source_dir = "/"

        @contextmanager
        def connect_for_download(self) -> Iterator[FakeDownloadConnection]:
            raise RuntimeError("Download disabled")

    client = Client.without_login(
        url="/",
        file_transfer=RaisingDownloader(fs=fs),
    )
    # Does not raise
    downloaded = client.download_files(
        dataset, target="./download", select=True, checksum_algorithm="md5"
    )
    assert all(file.local_path is not None for file in downloaded.files)


def test_override_datablock_checksum(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    # Ensure the file exists locally
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=True)

    # Downloads the same file again when the checksum algorithm is wrong.
    class RaisingDownloader(FakeFileTransfer):
        source_dir = "/"

        @contextmanager
        def connect_for_download(self) -> Iterator[FakeDownloadConnection]:
            raise RuntimeError("Download disabled")

    client = Client.without_login(
        url="/",
        file_transfer=RaisingDownloader(fs=fs),
    )
    with pytest.raises(RuntimeError, match="Download disabled"):
        client.download_files(
            dataset,
            target="./download",
            select=True,
            checksum_algorithm="sha256",  # The datablock uses md5
        )


def test_force_file_download(
    fs: FakeFilesystem, dataset_and_files: DatasetAndFiles
) -> None:
    # Ensure the file exists locally
    dataset, contents = dataset_and_files
    client = Client.without_login(
        url="/", file_transfer=FakeFileTransfer(fs=fs, files=contents)
    )
    client.download_files(dataset, target="./download", select=True)

    # Downloads the same file again with force=True.
    class RaisingDownloader(FakeFileTransfer):
        source_dir = "/"

        @contextmanager
        def connect_for_download(self) -> Iterator[FakeDownloadConnection]:
            raise RuntimeError("Download disabled")

    client = Client.without_login(
        url="/",
        file_transfer=RaisingDownloader(fs=fs),
    )
    with pytest.raises(RuntimeError, match="Download disabled"):
        client.download_files(
            dataset,
            target="./download",
            select=True,
            checksum_algorithm="md5",
            force=True,
        )
