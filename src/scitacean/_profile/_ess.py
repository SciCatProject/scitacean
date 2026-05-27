# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Profiles ESS SciCat instances."""

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
    )


def ess_staging_profile() -> Profile:
    return Profile(
        url="https://staging.scicat.ess.eu/api/v3",
        file_transfer=_ess_file_transfer(),
        frontend_url="https://staging.scicat.ess.eu",
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
