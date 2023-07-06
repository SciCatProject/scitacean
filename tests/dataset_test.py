# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from scitacean import PID, Dataset, DatasetType, File, model
from scitacean.testing import strategies as sst
from scitacean.testing.client import process_uploaded_dataset

from .common.files import make_file


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_new_dataset_has_no_files(typ):
    dset = Dataset(type=typ)
    assert len(list(dset.files)) == 0
    assert dset.number_of_files == 0
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 0


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_add_local_file_to_new_dataset(typ, fs):
    file_data = make_file(fs, "local/folder/data.dat")

    dset = Dataset(type=typ)
    dset.add_local_files("local/folder/data.dat")

    assert len(list(dset.files)) == 1
    assert dset.number_of_files == 1
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == file_data["size"]

    [f] = dset.files
    assert not f.is_on_remote
    assert f.is_on_local
    assert f.remote_access_path(dset.source_folder) is None
    assert f.local_path == Path("local/folder/data.dat")
    assert f.size == file_data["size"]
    assert f.checksum_algorithm == "blake2b"

    assert abs(file_data["creation_time"] - f.creation_time) < timedelta(seconds=1)
    assert abs(file_data["creation_time"] - f.make_model().time) < timedelta(seconds=1)


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_add_multiple_local_files_to_new_dataset(typ, fs):
    file_data0 = make_file(fs, "common/location1/data.dat")
    file_data1 = make_file(fs, "common/song.mp3")

    dset = Dataset(type=typ)
    dset.add_local_files("common/location1/data.dat", "common/song.mp3")

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == file_data0["size"] + file_data1["size"]

    [f0, f1] = dset.files
    if f0.local_path.suffix == ".mp3":
        f1, f0 = f0, f1

    assert not f0.is_on_remote
    assert f0.is_on_local
    assert f0.remote_access_path(dset.source_folder) is None
    assert f0.local_path == Path("common/location1/data.dat")
    assert f0.size == file_data0["size"]
    assert f0.checksum_algorithm == "blake2b"

    assert not f1.is_on_remote
    assert f1.is_on_local
    assert f1.remote_access_path(dset.source_folder) is None
    assert f1.local_path == Path("common/song.mp3")
    assert f1.size == file_data1["size"]
    assert f1.checksum_algorithm == "blake2b"


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_add_multiple_local_files_to_new_dataset_with_base_path(typ, fs):
    file_data0 = make_file(fs, "common/location1/data.dat")
    file_data1 = make_file(fs, "common/song.mp3")

    dset = Dataset(type=typ)
    dset.add_local_files(
        "common/location1/data.dat", "common/song.mp3", base_path="common"
    )

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == file_data0["size"] + file_data1["size"]

    [f0, f1] = dset.files
    if f0.local_path.suffix == ".mp3":
        f1, f0 = f0, f1

    assert not f0.is_on_remote
    assert f0.is_on_local
    assert f0.remote_access_path(dset.source_folder) is None
    assert f0.local_path == Path("common/location1/data.dat")
    assert f0.size == file_data0["size"]
    assert f0.checksum_algorithm == "blake2b"

    assert not f1.is_on_remote
    assert f1.is_on_local
    assert f1.remote_access_path(dset.source_folder) is None
    assert f1.local_path == Path("common/song.mp3")
    assert f1.size == file_data1["size"]
    assert f1.checksum_algorithm == "blake2b"


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
@pytest.mark.parametrize("algorithm", ("sha256", None))
def test_can_set_default_checksum_algorithm(typ, algorithm, fs):
    make_file(fs, "local/data.dat")

    dset = Dataset(type=typ, checksum_algorithm=algorithm)
    dset.add_local_files("local/data.dat")

    [f] = dset.files
    assert f.checksum_algorithm == algorithm


@given(sst.datasets(for_upload=True))
@settings(max_examples=100)
def test_dataset_models_roundtrip(initial):
    dataset_model = initial.make_upload_model()
    dblock_models = initial.make_datablock_upload_models().orig_datablocks
    dataset_model, dblock_models = process_uploaded_dataset(
        dataset_model, dblock_models
    )
    dataset_model.createdAt = None
    dataset_model.createdBy = None
    dataset_model.updatedAt = None
    dataset_model.updatedBy = None
    dataset_model.pid = None
    rebuilt = Dataset.from_download_models(
        dataset_model=dataset_model, orig_datablock_models=dblock_models
    )
    assert initial == rebuilt


@given(sst.datasets())
@settings(max_examples=10)
def test_make_scicat_models_datablock_without_files(dataset):
    assert dataset.make_datablock_upload_models().orig_datablocks is None


@given(sst.datasets(pid=st.builds(PID)))
@settings(max_examples=10)
def test_make_scicat_models_datablock_with_one_file(dataset):
    file_model = model.DownloadDataFile(
        path="path", size=6163, chk="8450ac0", gid="group", time=datetime.now()
    )
    dataset.add_files(File.from_scicat(local_path=None, model=file_model))

    blocks = dataset.make_datablock_upload_models().orig_datablocks
    assert len(blocks) == 1

    block = blocks[0]
    assert block.size == 6163
    assert block.datasetId == dataset.pid
    assert block.dataFileList == [model.UploadDataFile(**file_model.model_dump())]


@given(sst.datasets())
@settings(max_examples=10)
def test_eq_self(dset):
    dset.add_files(
        File.from_scicat(
            local_path=None,
            model=model.DownloadDataFile(path="path", size=94571, time=datetime.now()),
        )
    )
    assert dset == dset


# Fields whose types are not supported by hypothesis.
# E.g. because they contain `Any`.
_UNGENERATABLE_FIELDS = ("job_parameters", "meta")


# Filtering out bools because hypothesis struggles to find enough examples
# where the new value is not the same as the old value.
@pytest.mark.parametrize(
    "field",
    filter(
        lambda f: f.type != bool and f.name not in _UNGENERATABLE_FIELDS,
        Dataset.fields(read_only=False),
    ),
    ids=lambda f: f.name,
)
@given(sst.datasets(), st.data())
@settings(max_examples=10)
def test_neq_single_mismatched_field_writable(field, initial, data):
    new_val = data.draw(st.from_type(field.type))
    assume(new_val != getattr(initial, field.name))
    modified = initial.replace(**{field.name: new_val})
    assert modified != initial


@given(sst.datasets())
@settings(max_examples=10)
def test_neq_single_mismatched_file(initial):
    modified = initial.replace()
    modified.add_files(
        File.from_scicat(
            local_path=None,
            model=model.DownloadDataFile(
                path="path", size=51553312, time=datetime.now()
            ),
        )
    )
    initial.add_files(
        File.from_scicat(
            local_path=None,
            model=model.DownloadDataFile(path="path", size=94571, time=datetime.now()),
        )
    )
    assert modified != initial


@given(sst.datasets())
@settings(max_examples=10)
def test_neq_extra_file(initial):
    modified = initial.replace()
    modified.add_files(
        File.from_scicat(
            local_path="/local",
            model=model.DownloadDataFile(
                path="path", size=51553312, time=datetime.now()
            ),
        )
    )
    assert modified != initial


@pytest.mark.parametrize(
    "field",
    (
        field
        for field in Dataset.fields(read_only=False)
        if field.name not in _UNGENERATABLE_FIELDS
    ),
    ids=lambda f: f.name,
)
@given(sst.datasets(), st.data())
@settings(max_examples=5)
def test_replace_replaces_single_writable_field(field, initial, data):
    val = data.draw(st.from_type(field.type))
    replaced = initial.replace(**{field.name: val})
    assert getattr(replaced, field.name) == val


@pytest.mark.parametrize(
    "field",
    (
        field
        for field in Dataset.fields(read_only=True)
        if field.name
        not in (
            "history",
            "lifecycle",
            "number_of_files",
            "number_of_files_archived",
            "size",
            "packed_size",
        )
    ),
    ids=lambda f: f.name,
)
@given(sst.datasets(), st.data())
@settings(max_examples=5)
def test_replace_replaces_single_read_only_field(field, initial, data):
    val = data.draw(st.from_type(field.type))
    replaced = initial.replace(_read_only={field.name: val})
    assert getattr(replaced, field.name) == val


@given(sst.datasets())
@settings(max_examples=5)
def test_replace_replaces_multiple_fields(initial):
    replaced = initial.replace(
        owner="a-new-owner",
        used_software=["software1"],
        _read_only={"created_by": "the-creator"},
    )
    assert replaced.owner == "a-new-owner"
    assert replaced.used_software == ["software1"]
    assert replaced.created_by == "the-creator"


@given(sst.datasets())
@settings(max_examples=5)
def test_replace_other_fields_are_copied(initial):
    replaced = initial.replace(
        investigator="inv@esti.gator",
        techniques=[model.Technique(pid="tech/abcd.01", name="magick")],
        type="raw",
        _read_only={"api_version": 666},
    )
    assert replaced.owner == initial.owner
    assert replaced.size == initial.size
    assert replaced.updated_at == initial.updated_at
    assert replaced.history == initial.history


@given(sst.datasets())
@settings(max_examples=1)
def test_replace_rejects_bad_arguments(initial):
    with pytest.raises(TypeError):
        initial.replace(this_is_not_a_valid="argument", owner="the-owner-of-it-all")


@given(sst.datasets())
@settings(max_examples=1)
def test_replace_does_not_change_files_no_input_files(initial):
    replaced = initial.replace(owner="a-new-owner")
    assert replaced.number_of_files == 0
    assert replaced.size == 0
    assert list(replaced.files) == []


@given(sst.datasets())
@settings(max_examples=1)
def test_replace_does_not_change_files_with_input_files(initial):
    file = File.from_scicat(
        local_path=None,
        model=model.DownloadDataFile(path="path", size=6163, time=datetime.now()),
    )
    initial.add_files(file)
    replaced = initial.replace(owner="a-new-owner")
    assert replaced.number_of_files == 1
    assert replaced.size == 6163
    assert list(replaced.files) == list(initial.files)


@given(sst.datasets())
@settings(max_examples=5)
def test_as_new(initial):
    new = initial.as_new()
    assert new.created_at is None
    assert new.created_by is None
    assert new.updated_at is None
    assert new.updated_by is None
    assert new.history is None
    assert new.lifecycle is None
    assert abs(new.creation_time - datetime.now(tz=timezone.utc)) < timedelta(seconds=1)

    assert new.number_of_files == initial.number_of_files
    assert new.size == initial.size
    assert new.name == initial.name
    assert new.input_datasets == initial.input_datasets
    assert new.data_format == initial.data_format


@given(sst.datasets(pid=PID(pid="some-id")))
@settings(max_examples=5)
def test_derive_default(initial):
    derived = initial.derive()
    assert derived.type == "derived"
    assert derived.input_datasets == [initial.pid]
    assert derived.lifecycle is None
    assert derived.history is None

    assert derived.investigator == initial.investigator
    assert derived.owner == initial.owner
    assert derived.orcid_of_owner == initial.orcid_of_owner
    assert derived.owner_email == initial.owner_email
    assert derived.contact_email == initial.contact_email
    assert derived.techniques == initial.techniques

    assert derived.name is None
    assert derived.used_software is None
    assert derived.number_of_files == 0
    assert derived.number_of_files_archived == 0


@given(sst.datasets(pid=PID(pid="some-id")))
@settings(max_examples=5)
def test_derive_set_keep(initial):
    derived = initial.derive(keep=("name", "used_software"))
    assert derived.type == "derived"
    assert derived.input_datasets == [initial.pid]
    assert derived.lifecycle is None
    assert derived.history is None

    assert derived.name == initial.name
    assert derived.used_software == initial.used_software

    assert derived.number_of_files == 0
    assert derived.number_of_files_archived == 0


@given(sst.datasets(pid=PID(pid="some-id")))
@settings(max_examples=5)
def test_derive_keep_nothing(initial):
    derived = initial.derive(keep=())
    assert derived.type == "derived"
    assert derived.input_datasets == [initial.pid]
    assert derived.lifecycle is None
    assert derived.history is None

    assert derived.investigator is None
    assert derived.owner is None
    assert derived.name is None
    assert derived.used_software is None
    assert derived.number_of_files == 0
    assert derived.number_of_files_archived == 0


@given(sst.datasets(pid=None))
@settings(max_examples=5)
def test_derive_requires_pid(initial):
    with pytest.raises(ValueError):
        initial.derive()
