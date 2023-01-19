# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

# These tests use Dataset instead of DatasetFields in order to test the
# public interface and make sure that Dataset does not break any behavior.

from datetime import datetime, timedelta, timezone

import dateutil.parser
import pydantic
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scitacean import PID, Dataset, DatasetType
from scitacean.filesystem import RemotePath
from scitacean.model import DataFile, DerivedDataset, OrigDatablock, RawDataset


def test_init_dataset_with_only_type():
    dset = Dataset(type="raw")
    assert dset.type == DatasetType.RAW


@pytest.mark.parametrize(
    "typ", ("raw", "derived", DatasetType.RAW, DatasetType.DERIVED)
)
def test_init_dataset_accepted_types(typ):
    dset = Dataset(type=typ)
    assert dset.type == typ


def test_init_dataset_raises_for_bad_type():
    with pytest.raises(ValueError):
        Dataset(type="bad-type")  # type: ignore


def test_init_dataset_needs_type():
    with pytest.raises(TypeError):
        Dataset()  # type: ignore


def test_init_dataset_sets_creation_time():
    expected = datetime.now(tz=timezone.utc)
    dset = Dataset(type="raw")
    assert abs(dset.creation_time - expected) < timedelta(seconds=30)


def test_init_dataset_can_set_creation_time():
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
    assert abs(dset.creation_time - datetime.now(tz=timezone.utc)) < timedelta(
        seconds=30
    )


def test_init_dataset_default_values():
    dset = Dataset(type="derived")
    assert dset.history == []
    assert dset.is_published is False
    assert dset.meta == {}


@pytest.mark.parametrize("field", Dataset.fields(read_only=True), ids=lambda f: f.name)
def test_cannot_set_read_only_fields(field):
    dset = Dataset(type="raw")
    with pytest.raises(AttributeError):
        setattr(dset, field.name, None)


@pytest.mark.parametrize(
    "field",
    filter(lambda f: f.name != "type", Dataset.fields(read_only=False)),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_can_init_writable_fields(field, data):
    value = data.draw(st.from_type(field.type))
    dset = Dataset(type="raw", **{field.name: value})
    assert getattr(dset, field.name) == value


@pytest.mark.parametrize("field", Dataset.fields(read_only=False), ids=lambda f: f.name)
@given(st.data())
@settings(max_examples=10)
def test_can_set_writable_fields(field, data):
    value = data.draw(st.from_type(field.type))
    dset = Dataset(type="raw")
    setattr(dset, field.name, value)
    assert getattr(dset, field.name) == value


@pytest.mark.parametrize(
    "field",
    filter(lambda f: not f.read_only and f.name != "creation_time", Dataset.fields()),
    ids=lambda f: f.name,
)
def test_can_set_writable_fields_to_none(field):
    dset = Dataset(type="raw")
    setattr(dset, field.name, None)
    assert getattr(dset, field.name) is None


def test_cannot_set_creation_time_to_none():
    dset = Dataset(type="raw")
    with pytest.raises(TypeError):
        dset.creation_time = None


def test_init_from_models_sets_metadata():
    dset = Dataset.from_models(
        dataset_model=RawDataset(
            contactEmail="p.stibbons@uu.am",
            creationTime=dateutil.parser.parse("2022-01-10T11:14:52+02:00"),
            principalInvestigator="librarian@uu.am",
            owner="PonderStibbons",
            sourceFolder=RemotePath("/hex/source91"),
            type=DatasetType.RAW,
            ownerGroup="faculty",
            createdBy="pstibbons",
            createdAt=dateutil.parser.parse("2022-01-10T12:41:22+02:00"),
        ),
        orig_datablock_models=[
            OrigDatablock(
                dataFileList=[],
                size=0,
                ownerGroup="faculty",
            )
        ],
    )

    assert dset.contact_email == "p.stibbons@uu.am"
    assert dset.creation_time == dateutil.parser.parse("2022-01-10T11:14:52+02:00")
    assert dset.investigator == "librarian@uu.am"
    assert dset.owner == "PonderStibbons"
    assert dset.source_folder == "/hex/source91"
    assert dset.type == DatasetType.RAW
    assert dset.owner_group == "faculty"
    assert dset.created_by == "pstibbons"
    assert dset.created_at == dateutil.parser.parse("2022-01-10T12:41:22+02:00")

    assert dset.is_published is False
    assert dset.owner_email is None

    assert len(list(dset.files)) == 0
    assert dset.number_of_files == 0
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 0


def test_init_from_models_sets_files():
    dset = Dataset.from_models(
        dataset_model=RawDataset(
            contactEmail="p.stibbons@uu.am",
            creationTime=dateutil.parser.parse("2022-01-10T11:14:52-01:00"),
            principalInvestigator="librarian@uu.am",
            owner="PonderStibbons",
            sourceFolder=RemotePath("/hex/source91"),
            type=DatasetType.RAW,
            ownerGroup="faculty",
        ),
        orig_datablock_models=[
            OrigDatablock(
                dataFileList=[
                    DataFile(
                        path="file1.dat",
                        size=6123,
                        time=dateutil.parser.parse("2022-01-09T18:32:01-01:00"),
                    ),
                    DataFile(
                        path="sub/file2.png",
                        size=551,
                        time=dateutil.parser.parse("2022-01-09T18:32:42-01:00"),
                    ),
                ],
                size=6123 + 551,
                ownerGroup="faculty",
            )
        ],
    )

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 6123 + 551

    f0 = [f for f in dset.files if f.remote_path.suffix == ".dat"][0]
    assert f0.remote_access_path(dset.source_folder) == "/hex/source91/file1.dat"
    assert f0.local_path is None
    assert f0.size == 6123
    assert f0.make_model().path == "file1.dat"

    f1 = [f for f in dset.files if f.remote_path.suffix == ".png"][0]
    assert f1.remote_access_path(dset.source_folder) == "/hex/source91/sub/file2.png"
    assert f1.local_path is None
    assert f1.size == 551
    assert f1.make_model().path == "sub/file2.png"


def test_init_from_models_sets_files_multi_datablocks():
    dataset_model = RawDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=dateutil.parser.parse("2022-01-10T11:14:52-01:00"),
        principalInvestigator="librarian@uu.am",
        owner="PonderStibbons",
        sourceFolder=RemotePath("/hex/source91"),
        type=DatasetType.RAW,
        ownerGroup="faculty",
    )
    orig_datablock_models = [
        OrigDatablock(
            dataFileList=[
                DataFile(
                    path="file1.dat",
                    size=6123,
                )
            ],
            size=6123,
            ownerGroup="faculty",
        ),
        OrigDatablock(
            dataFileList=[
                DataFile(
                    path="sub/file2.png",
                    size=992,
                )
            ],
            size=992,
            ownerGroup="faculty",
        ),
    ]
    dset = Dataset.from_models(
        dataset_model=dataset_model,
        orig_datablock_models=orig_datablock_models,
    )

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 6123 + 992

    f0 = [f for f in dset.files if f.remote_path.suffix == ".dat"][0]
    assert f0.remote_access_path(dset.source_folder) == "/hex/source91/file1.dat"
    assert f0.local_path is None
    assert f0.size == 6123
    assert f0.make_model().path == "file1.dat"

    f1 = [f for f in dset.files if f.remote_path.suffix == ".png"][0]
    assert f1.remote_access_path(dset.source_folder) == "/hex/source91/sub/file2.png"
    assert f1.local_path is None
    assert f1.size == 992
    assert f1.make_model().path == "sub/file2.png"


def test_fields_type_filter_derived():
    assert all(
        field.used_by_derived for field in Dataset.fields(dataset_type="derived")
    )


def test_fields_type_filter_raw():
    assert all(field.used_by_raw for field in Dataset.fields(dataset_type="raw"))


def test_fields_read_only_filter_true():
    assert all(field.read_only for field in Dataset.fields(read_only=True))


def test_fields_read_only_filter_false():
    assert all(not field.read_only for field in Dataset.fields(read_only=False))


def test_fields_read_only__and_type_filter():
    assert all(
        not field.read_only and field.used_by_raw
        for field in Dataset.fields(read_only=False, dataset_type="raw")
    )


def test_make_raw_model():
    dset = Dataset(
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Ponder Stibbons;Mustrum Ridcully",
        owner_group="faculty",
        investigator="p.stibbons@uu.am",
        source_folder=RemotePath("/hex/source62"),
        creation_location="ANK/UU",
        shared_with=["librarian", "hicks"],
    )
    expected = RawDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=dateutil.parser.parse("2142-04-02T16:44:56"),
        owner="Ponder Stibbons;Mustrum Ridcully",
        ownerGroup="faculty",
        principalInvestigator="p.stibbons@uu.am",
        sourceFolder=RemotePath("/hex/source62"),
        type=DatasetType.RAW,
        history=[],
        isPublished=False,
        scientificMetadata={},
        creationLocation="ANK/UU",
        sharedWith=["librarian", "hicks"],
        numberOfFiles=0,
        numberOfFilesArchived=0,
        packedSize=0,
        size=0,
    )
    assert dset.make_model() == expected


def test_make_derived_model():
    dset = Dataset(
        type="derived",
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
    expected = DerivedDataset(
        contactEmail="p.stibbons@uu.am;m.ridcully@uu.am",
        creationTime=dateutil.parser.parse("2142-04-02T16:44:56"),
        owner="Ponder Stibbons;Mustrum Ridcully",
        ownerGroup="faculty",
        investigator="p.stibbons@uu.am",
        sourceFolder=RemotePath("/hex/source62"),
        type=DatasetType.DERIVED,
        history=[],
        isPublished=False,
        scientificMetadata={"weight": {"value": 5.23, "unit": "kg"}},
        inputDatasets=[PID(pid="623-122")],
        usedSoftware=["scitacean", "magick"],
        numberOfFiles=0,
        numberOfFilesArchived=0,
        packedSize=0,
        size=0,
    )
    assert dset.make_model() == expected


@pytest.mark.parametrize(
    "field",
    filter(
        lambda f: not f.used_by_raw,
        Dataset.fields(dataset_type="derived", read_only=False),
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_make_raw_model_raises_if_derived_field_set(field, data):
    dset = Dataset(
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Mustrum Ridcully",
        owner_group="faculty",
        investigator="p.stibbons@uu.am",
        source_folder=RemotePath("/hex/source62"),
    )
    setattr(dset, field.name, data.draw(st.from_type(field.type)))
    with pytest.raises(ValueError):
        dset.make_model()


@pytest.mark.parametrize(
    "field",
    filter(
        lambda f: not f.used_by_derived,
        Dataset.fields(dataset_type="raw", read_only=False),
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_make_derived_model_raises_if_raw_field_set(field, data):
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
    setattr(dset, field.name, data.draw(st.from_type(field.type)))
    with pytest.raises(ValueError):
        dset.make_model()


@pytest.mark.parametrize("field", ("contact_email", "investigator", "owner_email"))
def test_email_validation(field):
    dset = Dataset(
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Mustrum Ridcully",
        owner_group="faculty",
        investigator="p.stibbons@uu.am",
        source_folder=RemotePath("/hex/source62"),
    )
    setattr(dset, field, "not-an-email")
    with pytest.raises(pydantic.ValidationError):
        dset.make_model()


@pytest.mark.parametrize(
    "good_orcid",
    (
        "https://orcid.org/0000-0002-3761-3201",
        "https://orcid.org/0000-0001-2345-6789",
        "https://orcid.org/0000-0003-2818-0368",
    ),
)
def test_orcid_validation_valid(good_orcid):
    dset = Dataset(
        type="raw",
        contact_email="jan-lukas.wynen@ess.eu",
        creation_time="2142-04-02T16:44:56",
        owner="Jan-Lukas Wynen",
        owner_group="ess",
        investigator="jan-lukas.wynen@ess.eu",
        source_folder=RemotePath("/hex/source62"),
        orcid_of_owner=good_orcid,
    )
    assert dset.make_model().orcidOfOwner == good_orcid


@pytest.mark.parametrize(
    "bad_orcid",
    (
        "0000-0002-3761-3201",
        "https://not-orcid.eu/0000-0002-3761-3201",
        "https://orcid.org/0010-0002-3765-3201",
        "https://orcid.org/0000-0002-3761-320X",
    ),
)
def test_orcid_validation_missing_url(bad_orcid):
    dset = Dataset(
        type="raw",
        contact_email="jan-lukas.wynen@ess.eu",
        creation_time="2142-04-02T16:44:56",
        owner="Jan-Lukas Wynen",
        owner_group="ess",
        investigator="jan-lukas.wynen@ess.eu",
        source_folder=RemotePath("/hex/source62"),
        orcid_of_owner=bad_orcid,
    )
    with pytest.raises(pydantic.ValidationError):
        dset.make_model()


# TODO technique
