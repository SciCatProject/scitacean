# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="arg-type"

# These tests use Dataset instead of DatasetFields in order to test the
# public interface and make sure that Dataset does not break any behavior.

from datetime import datetime, timedelta, timezone

import dateutil.parser
import pydantic
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from scitacean import PID, Dataset, DatasetType
from scitacean.filesystem import RemotePath
from scitacean.model import (
    DownloadDataFile,
    DownloadDataset,
    DownloadOrigDatablock,
    UploadDerivedDataset,
    UploadRawDataset,
)

# Fields whose types are not supported by hypothesis.
# E.g. because they contain `Any`.
_UNGENERATABLE_FIELDS = ("job_parameters", "meta")
# Fields that are readonly, but still required in the constructor.
_NOT_SETTABLE_FIELDS = ("type",)


def test_init_dataset_with_only_type() -> None:
    dset = Dataset(type="raw")
    assert dset.type == DatasetType.RAW


@pytest.mark.parametrize(
    "typ", ["raw", "derived", DatasetType.RAW, DatasetType.DERIVED]
)
def test_init_dataset_accepted_types(typ: str | DatasetType) -> None:
    dset = Dataset(type=typ)
    assert dset.type == typ


def test_init_dataset_raises_for_bad_type() -> None:
    with pytest.raises(ValueError, match="DatasetType"):
        Dataset(type="bad-type")  # type: ignore[arg-type]


def test_init_dataset_needs_type() -> None:
    with pytest.raises(TypeError):
        Dataset()  # type: ignore[call-arg]


def test_init_dataset_sets_creation_time() -> None:
    expected = datetime.now(tz=timezone.utc)
    dset = Dataset(type="raw")
    assert dset.creation_time is not None
    assert abs(dset.creation_time - expected) < timedelta(seconds=30)


def test_init_dataset_can_set_creation_time() -> None:
    dt: str | datetime

    dt = dateutil.parser.parse("2022-01-10T11:14:52.623Z")
    dset = Dataset(type="derived", creation_time=dt)
    assert dset.creation_time == dt

    dt = dateutil.parser.parse("2022-01-10T11:14:52+02:00")
    dset = Dataset(type="derived", creation_time=dt)
    assert dset.creation_time == dt

    dt = "1994-03-21T22:51:33-01:00"
    dset = Dataset(type="derived", creation_time=dt)
    assert dset.creation_time == dateutil.parser.parse(dt)

    dset = Dataset(type="derived", creation_time="now")
    assert dset.creation_time is not None
    assert abs(dset.creation_time - datetime.now(tz=timezone.utc)) < timedelta(
        seconds=30
    )


@pytest.mark.parametrize("field", Dataset.fields(read_only=True), ids=lambda f: f.name)
def test_cannot_set_read_only_fields(field: Dataset.Field) -> None:
    dset = Dataset(type="raw")
    with pytest.raises(AttributeError):
        setattr(dset, field.name, None)


@pytest.mark.parametrize(
    "field",
    (
        f
        for f in Dataset.fields(read_only=False)
        if f.name not in ("type", *_UNGENERATABLE_FIELDS)
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_can_init_writable_fields(field: Dataset.Field, data: st.DataObject) -> None:
    value = data.draw(st.from_type(field.type))
    dset = Dataset(type="raw", **{field.name: value})
    assert getattr(dset, field.name) == value


@pytest.mark.parametrize(
    "field",
    (
        f
        for f in Dataset.fields(read_only=False)
        if f.name not in _UNGENERATABLE_FIELDS and f.name not in _NOT_SETTABLE_FIELDS
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_can_set_writable_fields(field: Dataset.Field, data: st.DataObject) -> None:
    value = data.draw(st.from_type(field.type))
    dset = Dataset(type="raw")
    setattr(dset, field.name, value)
    assert getattr(dset, field.name) == value


@pytest.mark.parametrize(
    "field",
    (f for f in Dataset.fields() if f.name != "type" and not f.read_only),
    ids=lambda f: f.name,
)
def test_can_set_writable_fields_to_none(field: Dataset.Field) -> None:
    dset = Dataset(type="raw")
    setattr(dset, field.name, None)
    assert getattr(dset, field.name) is None


def test_init_from_models_sets_metadata() -> None:
    dset = Dataset.from_download_models(
        dataset_model=DownloadDataset(
            contactEmail="p.stibbons@uu.am",
            creationTime=dateutil.parser.parse("2022-01-10T11:14:52+02:00"),
            numberOfFiles=0,
            numberOfFilesArchived=0,
            packedSize=0,
            pid=PID.parse("prefix/0123-ab"),
            principalInvestigator="my principal investigator",
            owner="PonderStibbons",
            size=0,
            sourceFolder=RemotePath("/hex/source91"),
            type=DatasetType.RAW,
            ownerGroup="faculty",
            createdBy="pstibbons",
            createdAt=dateutil.parser.parse("2022-01-10T12:41:22+02:00"),
        ),
        orig_datablock_models=[
            DownloadOrigDatablock(
                dataFileList=[],
                datasetId=PID.parse("prefix/0123-ab"),
                size=0,
                ownerGroup="faculty",
                chkAlg="md5",
            )
        ],
    )

    assert dset.contact_email == "p.stibbons@uu.am"
    assert dset.creation_time == dateutil.parser.parse("2022-01-10T11:14:52+02:00")
    assert dset.principal_investigator == "my principal investigator"
    assert dset.owner == "PonderStibbons"
    assert dset.source_folder == "/hex/source91"
    assert dset.type == DatasetType.RAW
    assert dset.owner_group == "faculty"
    assert dset.created_by == "pstibbons"
    assert dset.created_at == dateutil.parser.parse("2022-01-10T12:41:22+02:00")

    assert dset.is_published is None
    assert dset.owner_email is None

    assert len(list(dset.files)) == 0
    assert dset.number_of_files == 0
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 0


def test_init_from_models_sets_files() -> None:
    dset = Dataset.from_download_models(
        dataset_model=DownloadDataset(
            contactEmail="p.stibbons@uu.am",
            creationTime=dateutil.parser.parse("2022-01-10T11:14:52-01:00"),
            numberOfFiles=2,
            numberOfFilesArchived=0,
            principalInvestigator="librarian@uu.am",
            owner="PonderStibbons",
            size=6123 + 551,
            packedSize=0,
            pid=PID.parse("prefix/abcd-de"),
            sourceFolder=RemotePath("/hex/source91"),
            type=DatasetType.RAW,
            ownerGroup="faculty",
        ),
        orig_datablock_models=[
            DownloadOrigDatablock(
                dataFileList=[
                    DownloadDataFile(
                        path="file1.dat",
                        size=6123,
                        time=dateutil.parser.parse("2022-01-09T18:32:01-01:00"),
                    ),
                    DownloadDataFile(
                        path="sub/file2.png",
                        size=551,
                        time=dateutil.parser.parse("2022-01-09T18:32:42-01:00"),
                    ),
                ],
                size=6123 + 551,
                ownerGroup="faculty",
                datasetId=PID.parse("prefix/abcd-de"),
                chkAlg="md5",
            )
        ],
    )

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 6123 + 551

    (f0,) = (f for f in dset.files if f.remote_path.suffix == ".dat")
    assert f0.remote_access_path(dset.source_folder) == "/hex/source91/file1.dat"
    assert f0.local_path is None
    assert f0.size == 6123
    assert f0.make_model().path == "file1.dat"

    (f1,) = (f for f in dset.files if f.remote_path.suffix == ".png")
    assert f1.remote_access_path(dset.source_folder) == "/hex/source91/sub/file2.png"
    assert f1.local_path is None
    assert f1.size == 551
    assert f1.make_model().path == "sub/file2.png"


def test_init_from_models_sets_files_multi_datablocks() -> None:
    dataset_model = DownloadDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=dateutil.parser.parse("2022-01-10T11:14:52-01:00"),
        numberOfFiles=2,
        numberOfFilesArchived=0,
        packedSize=0,
        pid=PID.parse("prefix/abcd-de"),
        principalInvestigator="librarian@uu.am",
        owner="PonderStibbons",
        size=6123 + 992,
        sourceFolder=RemotePath("/hex/source91"),
        type=DatasetType.RAW,
        ownerGroup="faculty",
    )
    orig_datablock_models = [
        DownloadOrigDatablock(
            dataFileList=[
                DownloadDataFile(
                    path="file1.dat",
                    size=6123,
                    time=dateutil.parser.parse("2022-01-10T11:14:52-01:00"),
                )
            ],
            datasetId=PID.parse("prefix/abcd-de"),
            size=6123,
            ownerGroup="faculty",
            chkAlg="md5",
        ),
        DownloadOrigDatablock(
            dataFileList=[
                DownloadDataFile(
                    path="sub/file2.png",
                    size=992,
                    time=dateutil.parser.parse("2022-01-10T11:14:52-01:00"),
                )
            ],
            datasetId=PID.parse("prefix/abcd-de"),
            size=992,
            ownerGroup="faculty",
            chkAlg="md5",
        ),
    ]
    dset = Dataset.from_download_models(
        dataset_model=dataset_model,
        orig_datablock_models=orig_datablock_models,
    )

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 6123 + 992

    (f0,) = (f for f in dset.files if f.remote_path.suffix == ".dat")
    assert f0.remote_access_path(dset.source_folder) == "/hex/source91/file1.dat"
    assert f0.local_path is None
    assert f0.size == 6123
    assert f0.make_model().path == "file1.dat"

    (f1,) = (f for f in dset.files if f.remote_path.suffix == ".png")
    assert f1.remote_access_path(dset.source_folder) == "/hex/source91/sub/file2.png"
    assert f1.local_path is None
    assert f1.size == 992
    assert f1.make_model().path == "sub/file2.png"


def test_fields_type_filter_derived() -> None:
    assert all(
        field.used_by_derived for field in Dataset.fields(dataset_type="derived")
    )


def test_fields_type_filter_raw() -> None:
    assert all(field.used_by_raw for field in Dataset.fields(dataset_type="raw"))


def test_fields_read_only_filter_true() -> None:
    assert all(field.read_only for field in Dataset.fields(read_only=True))


def test_fields_read_only_filter_false() -> None:
    assert all(not field.read_only for field in Dataset.fields(read_only=False))


def test_fields_read_only__and_type_filter() -> None:
    assert all(
        not field.read_only and field.used_by_raw
        for field in Dataset.fields(read_only=False, dataset_type="raw")
    )


def test_make_raw_model() -> None:
    dset = Dataset(
        name="raw-dataset-62",
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Ponder Stibbons;Mustrum Ridcully",
        owner_group="faculty",
        principal_investigator="my principal investigator",
        source_folder=RemotePath("/hex/source62"),
        creation_location="ANK/UU",
        shared_with=["librarian", "hicks"],
        used_software=["scitacean"],
    )
    expected = UploadRawDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=dateutil.parser.parse("2142-04-02T16:44:56"),
        datasetName="raw-dataset-62",
        owner="Ponder Stibbons;Mustrum Ridcully",
        ownerGroup="faculty",
        principalInvestigator="my principal investigator",
        sourceFolder=RemotePath("/hex/source62"),
        type=DatasetType.RAW,
        scientificMetadata=None,
        creationLocation="ANK/UU",
        sharedWith=["librarian", "hicks"],
        numberOfFiles=0,
        numberOfFilesArchived=0,
        packedSize=0,
        size=0,
        inputDatasets=[],
        usedSoftware=["scitacean"],
    )
    assert dset.make_upload_model() == expected


def test_make_derived_model() -> None:
    dset = Dataset(
        type="derived",
        name="derived-dataset",
        contact_email="p.stibbons@uu.am;m.ridcully@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Ponder Stibbons;Mustrum Ridcully",
        owner_group="faculty",
        investigator="p.stibbons@uu.am",
        source_folder=RemotePath("/hex/source62"),
        meta={"weight": {"value": 5.23, "unit": "kg"}},
        input_datasets=[PID(pid="623-122")],
        used_software=["scitacean", "magick"],
    )
    expected = UploadDerivedDataset(
        datasetName="derived-dataset",
        contactEmail="p.stibbons@uu.am;m.ridcully@uu.am",
        creationTime=dateutil.parser.parse("2142-04-02T16:44:56"),
        owner="Ponder Stibbons;Mustrum Ridcully",
        ownerGroup="faculty",
        investigator="p.stibbons@uu.am",
        sourceFolder=RemotePath("/hex/source62"),
        type=DatasetType.DERIVED,
        isPublished=None,
        scientificMetadata={"weight": {"value": 5.23, "unit": "kg"}},
        inputDatasets=[PID(pid="623-122")],
        usedSoftware=["scitacean", "magick"],
        numberOfFiles=0,
        numberOfFilesArchived=0,
        packedSize=0,
        size=0,
    )
    assert dset.make_upload_model() == expected


@pytest.mark.parametrize(
    "field",
    (
        f
        for f in Dataset.fields(dataset_type="derived", read_only=False)
        if not f.used_by_raw and f.name not in _UNGENERATABLE_FIELDS
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_make_raw_model_raises_if_derived_field_set(
    field: Dataset.Field, data: st.DataObject
) -> None:
    dset = Dataset(
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Mustrum Ridcully",
        owner_group="faculty",
        principal_investigator="p.stibbons@uu.am",
        source_folder=RemotePath("/hex/source62"),
    )
    val = data.draw(st.from_type(field.type))
    assume(val is not None)
    with pytest.raises(pydantic.ValidationError):
        dset.make_upload_model()


@pytest.mark.parametrize(
    "field",
    (
        f
        for f in Dataset.fields(dataset_type="raw", read_only=False)
        if not f.used_by_derived and f.name not in _UNGENERATABLE_FIELDS
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_make_derived_model_raises_if_raw_field_set(
    field: Dataset.Field, data: st.DataObject
) -> None:
    dset = Dataset(
        type="derived",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Ponder Stibbons",
        owner_group="faculty",
        investigator="p.stibbons@uu.am",
        source_folder=RemotePath("/hex/source62"),
        input_datasets=[PID(pid="623-122")],
        used_software=["scitacean", "magick"],
    )
    val = data.draw(st.from_type(field.type))
    assume(val is not None)
    setattr(dset, field.name, val)
    with pytest.raises(pydantic.ValidationError):
        dset.make_upload_model()


@pytest.mark.parametrize("field", ["contact_email", "owner_email"])
def test_email_validation(field: Dataset.Field) -> None:
    dset = Dataset(
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Mustrum Ridcully",
        owner_group="faculty",
        principal_investigator="p.stibbons@uu.am",
        source_folder=RemotePath("/hex/source62"),
    )
    setattr(dset, field, "not-an-email")
    with pytest.raises(pydantic.ValidationError):
        dset.make_upload_model()


@pytest.mark.parametrize(
    "good_orcid",
    [
        "https://orcid.org/0000-0002-3761-3201",
        "https://orcid.org/0000-0001-2345-6789",
        "https://orcid.org/0000-0003-2818-0368",
    ],
)
def test_orcid_validation_valid(good_orcid: str) -> None:
    dset = Dataset(
        type="raw",
        name="test ORCID",
        contact_email="jan-lukas.wynen@ess.eu",
        creation_location="scitacean/tests",
        creation_time="2142-04-02T16:44:56",
        owner="Jan-Lukas Wynen",
        owner_group="ess",
        principal_investigator="jan-lukas.wynen@ess.eu",
        source_folder=RemotePath("/hex/source62"),
        orcid_of_owner=good_orcid,
    )
    assert dset.make_upload_model().orcidOfOwner == good_orcid


@pytest.mark.parametrize(
    "bad_orcid",
    [
        "0000-0002-3761-3201",
        "https://not-orcid.eu/0000-0002-3761-3201",
        "https://orcid.org/0010-0002-3765-3201",
        "https://orcid.org/0000-0002-3761-320X",
    ],
)
def test_orcid_validation_missing_url(bad_orcid: str) -> None:
    dset = Dataset(
        type="raw",
        contact_email="jan-lukas.wynen@ess.eu",
        creation_time="2142-04-02T16:44:56",
        owner="Jan-Lukas Wynen",
        owner_group="ess",
        principal_investigator="jan-lukas.wynen@ess.eu",
        source_folder=RemotePath("/hex/source62"),
        orcid_of_owner=bad_orcid,
    )
    with pytest.raises(pydantic.ValidationError):
        dset.make_upload_model()


# TODO technique
