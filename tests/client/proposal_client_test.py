# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

import dataclasses
from datetime import UTC, datetime

import pytest

from scitacean import Client, ScicatCommError
from scitacean.client import ScicatClient
from scitacean.model import (
    DownloadProposal,
    MeasurementPeriod,
    Proposal,
    UploadProposal,
)
from scitacean.testing.backend import config as backend_config


# Creating proposals requires at least ingestor permissions.
@pytest.fixture
def ingestor_access(
    scicat_access: backend_config.SciCatAccess,
) -> backend_config.SciCatAccess:
    return backend_config.SciCatAccess(
        url=scicat_access.url,
        user=backend_config.USERS["ingestor"],
    )


# Override the default real_client fixture to use ingestor permissions.
@pytest.fixture
def real_client(
    request: pytest.FixtureRequest,
    ingestor_access: backend_config.SciCatAccess,
    scicat_backend: bool,
) -> Client:
    pytest.skip("No available user can create proposals.")
    # skip_if_not_backend(request)
    # return Client.from_credentials(
    #     url=ingestor_access.url,
    #     **ingestor_access.user.credentials,
    # )


@pytest.fixture
def scicat_client(client: Client) -> ScicatClient:
    return client.scicat


@pytest.fixture
def proposal(ingestor_access: backend_config.SciCatAccess) -> Proposal:
    scicat_access = ingestor_access
    return Proposal(
        email=scicat_access.user.email,
        owner_group=scicat_access.user.group,
        proposal_id="123def",
        title="A test proposal",
        access_groups=["group1", "second_group"],
        pi_email="principal@investigator.net",
        pi_firstname="John",
        pi_lastname="Principal",
        measurement_period_list=[
            MeasurementPeriod(
                start=datetime(2022, 11, 16, 15, 6, 2, tzinfo=UTC),
                end=datetime(2022, 11, 17, 8, 0, 50, tzinfo=UTC),
                instrument="Neutrometer",
            )
        ],
    )


def compare_proposal_model_after_upload(
    uploaded: UploadProposal | DownloadProposal, downloaded: DownloadProposal
) -> None:
    for key, expected in uploaded:
        # The database populates a number of fields that are None in uploaded.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None:
            assert expected == dict(downloaded)[key], f"key = {key}"


def compare_proposal_after_upload(uploaded: Proposal, downloaded: Proposal) -> None:
    for field in dataclasses.fields(uploaded):
        # The database populates a number of fields that are None in uploaded.
        # But we don't want to test those here as we don't want to test the database.
        expected = getattr(uploaded, field.name)
        if expected is not None:
            assert expected == getattr(downloaded, field.name), f"key = {field.name}"


def test_create_proposal_model_roundtrip(
    scicat_client: ScicatClient, proposal: Proposal
) -> None:
    upload_proposal = proposal.make_upload_model()
    finalized = scicat_client.create_proposal_model(upload_proposal)
    assert finalized.proposalId == proposal.proposal_id
    downloaded = scicat_client.get_proposal_model(finalized.proposalId)
    compare_proposal_model_after_upload(upload_proposal, downloaded)
    compare_proposal_model_after_upload(finalized, downloaded)


def test_create_sample_model_roundtrip_existing_id(
    scicat_client: ScicatClient, proposal: Proposal
) -> None:
    upload_proposal = proposal.make_upload_model()
    finalized = scicat_client.create_proposal_model(upload_proposal)
    assert finalized.proposalId is not None
    upload_proposal.proposalId = finalized.proposalId
    # SciCat might accept an identical proposal, so change it.
    upload_proposal.abstract = "A new proposal with the same id"
    with pytest.raises(ScicatCommError):
        scicat_client.create_proposal_model(upload_proposal)
