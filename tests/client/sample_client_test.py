# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import pytest

from scitacean import Client, ScicatCommError
from scitacean.client import ScicatClient
from scitacean.model import (
    Sample,
)


@pytest.fixture()
def scicat_client(client: Client) -> ScicatClient:
    return client.scicat


@pytest.fixture()
def sample(scicat_access):
    return Sample(
        owner_group=scicat_access.user.group,
        access_groups=["group1", "2nd_group"],
        description="A test sample for Scitacean",
        owner="ridcully",
        sample_characteristics={"layers": ["H2O", "EtOH"], "mass": 2},
    )


def compare_sample_after_upload(uploaded, downloaded):
    for key, expected in uploaded:
        # The database populates a number of fields that are None in uploaded.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None:
            assert expected == dict(downloaded)[key], f"key = {key}"


def test_create_sample_model_roundtrip(scicat_client, sample):
    upload_sample = sample.make_upload_model()
    finalized = scicat_client.create_sample_model(upload_sample)
    downloaded = scicat_client.get_sample_model(finalized.sampleId)
    compare_sample_after_upload(upload_sample, downloaded)
    compare_sample_after_upload(finalized, downloaded)


def test_create_sample_model_roundtrip_existing_id(scicat_client, sample):
    upload_sample = sample.make_upload_model()
    upload_sample.sampleId = "my-sample-id"
    scicat_client.create_sample_model(upload_sample)
    with pytest.raises(ScicatCommError):
        scicat_client.create_sample_model(upload_sample)


def test_create_sample_model_populates_id(scicat_client, sample):
    upload_sample = sample.make_upload_model()
    finalized = scicat_client.create_sample_model(upload_sample)
    downloaded = scicat_client.get_sample_model(finalized.sampleId)
    assert finalized.sampleId is not None
    assert downloaded.sampleId == finalized.sampleId
