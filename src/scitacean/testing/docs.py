"""
Utilities for the documentation.

Should probably not be used externally.
"""

from dateutil.parser import parse as parse_date

from ..filesystem import RemotePath
from ..model import DataFile, DatasetType, OrigDatablock, RawDataset
from ..pid import PID
from .client import FakeClient
from .transfer import FakeFileTransfer


def _create_raw_dataset(client: FakeClient) -> None:
    content1 = b"5 4 9 11 15 12 7 6 1"
    content2 = (
        b"INFO Starting measurement\nWARN Detector saturated\nINFO Measurement finished"
    )
    client.file_transfer.files["/hex/ps/thaum/flux.dat"] = content1
    client.file_transfer.files["/hex/ps/thaum/logs/measurement.log"] = content2

    dataset_id = PID(prefix="20.500.12269", pid="72fe3ff6-105b-4c7f-b9d0-073b67c90ec3")
    client.datasets[dataset_id] = RawDataset(
        pid=dataset_id,
        datasetName="Thaum flux",
        description="Measured the thaum flux",
        createdBy="Ponder Stibbons",
        updatedBy="anonymous",
        updatedAt=parse_date("2022-11-01T13:22:08.927Z"),
        createdAt=parse_date("2022-08-17T14:20:23.675Z"),
        owner="Ponder Stibbons",
        ownerGroup="uu",
        accessGroups=["faculty"],
        principalInvestigator="p.stibbons@uu.am",
        contactEmail="p.stibbons@uu.am",
        creationTime=parse_date("2022-06-29T14:01:05.000Z"),
        numberOfFiles=2,
        size=len(content1) + len(content2),
        sourceFolder=RemotePath("/hex/ps/thaum"),
        scientificMetadata={
            "data_type": "histogram",
            "temperature": {"value": "123", "unit": "K"},
        },
        type=DatasetType.RAW,
    )
    client.orig_datablocks[dataset_id] = [
        OrigDatablock(
            id=PID(prefix="20.500.12269", pid="02dc390c-811c-4d6a-93bf-9f85a4214ca0"),
            datasetId=dataset_id,
            size=len(content1) + len(content2),
            ownerGroup="uu",
            accessGroups=["faculty"],
            dataFileList=[
                DataFile(
                    path="flux.dat",
                    size=len(content1),
                    time=parse_date("2022-08-17T13:54:12Z"),
                ),
                DataFile(
                    path="logs/measurement.log",
                    size=len(content2),
                    time=parse_date("2022-08-17T13:55:21Z"),
                ),
            ],
        )
    ]


def setup_fake_client() -> FakeClient:
    client = FakeClient.from_token(
        url="fake-url.sci/api/v3",
        token="fake-token",  # noqa: S106
        file_transfer=FakeFileTransfer(fs=None),
    )
    _create_raw_dataset(client)

    return client
