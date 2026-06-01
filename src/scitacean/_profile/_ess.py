# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Profiles ESS SciCat instances."""

from collections.abc import Callable, Iterable
from typing import Any

from ..transfer.copy import CopyFileTransfer
from ..transfer.link import LinkFileTransfer
from ..transfer.select import SelectFileTransfer
from ..typing import FileTransfer
from ._common import Profile


def ess_production_profile() -> Profile:
    return Profile(
        url="https://scicat.ess.eu/api/v3",
        file_transfer=_ess_file_transfer(),
        frontend_url="https://scicat.ess.eu",
        scientific_metadata_schema="value-unit",
        field_factories=_ess_field_factories(),
    )


def ess_staging_profile() -> Profile:
    return Profile(
        url="https://staging.scicat.ess.eu/api/v3",
        file_transfer=_ess_file_transfer(),
        frontend_url="https://staging.scicat.ess.eu",
        scientific_metadata_schema="value-unit",
        field_factories=_ess_field_factories(),
    )


profiles = (
    ("ess", ess_production_profile),
    ("staging.ess", ess_staging_profile),
)


def _ess_file_transfer() -> FileTransfer:
    children: list[FileTransfer] = [
        LinkFileTransfer(),
        CopyFileTransfer(),
    ]

    try:
        from ..transfer.sftp import SFTPFileTransfer

        children.append(SFTPFileTransfer(host="login.esss.dk"))
    except ModuleNotFoundError as err:
        from ..logging import get_logger

        get_logger().warning(
            "SFTP is not available, only file transfers on the same system "
            "are supported. Error: %s",
            err,
        )

    return SelectFileTransfer(children)


def _ess_field_factories() -> dict[str, Callable[..., Any]]:
    return {
        "creationLocation": _format_creation_location,
        "ownerGroup": _format_owner_group,
        "sourceFolder": _format_source_folder,
    }


def _format_creation_location(instrumentNames: Iterable[str]) -> str | None:
    try:
        [name] = instrumentNames
    except ValueError:
        return None

    match name.lower():
        case "loki":
            return "ESS:LoKI"
        case _:
            return f"ESS:{str(name).strip().upper()}"


def _format_owner_group(proposalIds: Iterable[str]) -> str | None:
    try:
        [proposal_id] = proposalIds
    except ValueError:
        return None

    return str(proposal_id).strip()


def _format_source_folder(
    proposalIds: Iterable[str], instrumentNames: Iterable[str]
) -> str | None:
    try:
        [proposal_id] = proposalIds
    except ValueError:
        return None
    try:
        [instrument_name] = instrumentNames
    except ValueError:
        return None

    return f"/ess/data/{proposal_id}/{str(instrument_name).strip().lower()}/upload"
