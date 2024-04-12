# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import dataclasses

import pytest

from scitacean import Client, ScicatCommError
from scitacean.client import ScicatClient
from scitacean.model import (
    Sample,
)
from scitacean.testing.backend import config as backend_config
from scitacean.testing.backend import skip_if_not_backend


# Creating samples requires at least ingestor permissions.
@pytest.fixture()
def ingestor_access(
    scicat_access: backend_config.SciCatAccess,
) -> backend_config.SciCatAccess:
    return backend_config.SciCatAccess(
        url=scicat_access.url,
        user=backend_config.USERS["ingestor"],
    )


@pytest.fixture()
def real_client(
    request: pytest.FixtureRequest,
    ingestor_access: backend_config.SciCatAccess,
    scicat_backend: bool,
) -> Client:
    skip_if_not_backend(request)
    return Client.from_credentials(
        url=ingestor_access.url,
        **ingestor_access.user.credentials,  # type: ignore[arg-type]
    )


@pytest.fixture()
def scicat_client(client: Client) -> ScicatClient:
    return client.scicat


@pytest.fixture()
def sample(ingestor_access):
    scicat_access = ingestor_access
    return Sample(
        owner_group=scicat_access.user.group,
        access_groups=["group1", "2nd_group"],
        description="A test sample for Scitacean",
        owner=scicat_access.user.username,
        sample_characteristics={"layers": ["H2O", "EtOH"], "mass": 2},
    )


def compare_sample_model_after_upload(uploaded, downloaded):
    for key, expected in uploaded:
        # The database populates a number of fields that are None in uploaded.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None:
            assert expected == dict(downloaded)[key], f"key = {key}"


def compare_sample_after_upload(uploaded, downloaded):
    for field in dataclasses.fields(uploaded):
        # The database populates a number of fields that are None in uploaded.
        # But we don't want to test those here as we don't want to test the database.
        expected = getattr(uploaded, field.name)
        if expected is not None:
            assert expected == getattr(downloaded, field.name), f"key = {field.name}"


@pytest.mark.skip("Sample creation does not currently work")
def test_create_sample_model_roundtrip(scicat_client, sample):
    upload_sample = sample.make_upload_model()
    finalized = scicat_client.create_sample_model(upload_sample)
    downloaded = scicat_client.get_sample_model(finalized.sampleId)
    compare_sample_model_after_upload(upload_sample, downloaded)
    compare_sample_model_after_upload(finalized, downloaded)


@pytest.mark.skip("Sample creation does not currently work")
def test_create_sample_model_roundtrip_existing_id(scicat_client, sample):
    upload_sample = sample.make_upload_model()
    finalized = scicat_client.create_sample_model(upload_sample)
    upload_sample.sampleId = finalized.sampleId
    # SciCat might accept an identical sample, so change it.
    upload_sample.description = "A new sample with the same id"
    with pytest.raises(ScicatCommError):
        scicat_client.create_sample_model(upload_sample)


@pytest.mark.skip("Sample creation does not currently work")
def test_create_sample_model_populates_id(scicat_client, sample):
    upload_sample = sample.make_upload_model()
    finalized = scicat_client.create_sample_model(upload_sample)
    downloaded = scicat_client.get_sample_model(finalized.sampleId)
    assert finalized.sampleId is not None
    assert downloaded.sampleId == finalized.sampleId


@pytest.mark.skip("Sample creation does not currently work")
def test_upload_sample_roundtrip(client, sample):
    finalized = client.upload_new_sample_now(sample)
    compare_sample_after_upload(sample, finalized)


@pytest.mark.skip("Sample creation does not currently work")
def test_upload_sample_overrides_id(client, sample):
    sample.sample_id = "my_sample-id"
    finalized = client.upload_new_sample_now(sample)
    assert finalized.sample_id != sample.sample_id
