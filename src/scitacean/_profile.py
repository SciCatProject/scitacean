# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Profiles for connecting to SciCat."""

from dataclasses import dataclass
from pathlib import Path

import tomli

from .transfer.copy import CopyFileTransfer
from .transfer.link import LinkFileTransfer
from .transfer.select import SelectFileTransfer
from .transfer.sftp import SFTPFileTransfer
from .typing import FileTransfer


@dataclass(frozen=True, slots=True)
class Profile:
    """Parameters for connecting to a specific instance of SciCat.

    The fields of a profile correspond to the arguments of the constructors
    of :class:`Client`.
    They can be overridden by the explicit constructor arguments.

    When constructing a client from a profile, the ``profile`` argument may be one of:

    - If ``profile`` is a :class:`Profile`, it is returned as is.
    - If ``profile`` is a :class:`pathlib.Path`, a profile is loaded from
      the file at that path.
    - If ``profile`` is a :class:`str`
        * and ``profile`` matches the name of a builtin profile,
          that profile is returned.
        * Otherwise, a profile is loaded from a file with this path, potentially
          by appending ``".profile.toml"`` to the name.
    """

    url: str
    """URL of the SciCat API.

    Note that this is the URL to the API, *not* the web interface.
    For example, at ESS, the web interface URL is ``"https://scicat.ess.eu"``.
    But the API URL is ``"https://scicat.ess.eu/api/v3"`` (at the time of writing).
    """
    file_transfer: FileTransfer | None
    """A file transfer object for uploading and downloading files.

    See the `File transfer <../../reference/index.rst#file-transfer>`_. section for
    implementations provided by Scitacean.
    """


def locate_profile(spec: str | Path | Profile) -> Profile:
    """Find and return a specified profile."""
    if isinstance(spec, Profile):
        return spec

    if isinstance(spec, Path):
        return _load_profile_from_file(spec)

    try:
        return _builtin_profile(spec)
    except KeyError:
        pass

    try:
        return _load_profile_from_file(spec)
    except FileNotFoundError:
        if spec.endswith(".profile.toml"):
            raise ValueError(f"Unknown profile: {spec}") from None

    try:
        return _load_profile_from_file(f"{spec}.profile.toml")
    except FileNotFoundError:
        raise ValueError(f"Unknown profile: {spec}") from None


def _builtin_profile(name: str) -> Profile:
    match name:
        case "ess":
            return Profile(
                url="https://scicat.ess.eu/api/v3", file_transfer=_ess_file_transfer()
            )
        case "staging.ess":
            return Profile(
                url="https://staging.scicat.ess.eu/api/v3",
                file_transfer=_ess_file_transfer(),
            )
    raise KeyError(f"Unknown builtin profile: {name}")


def _ess_file_transfer() -> FileTransfer:
    return SelectFileTransfer(
        [
            LinkFileTransfer(),
            CopyFileTransfer(),
            SFTPFileTransfer(host="login.esss.dk"),
        ]
    )


def _load_profile_from_file(name: str | Path) -> Profile:
    with open(name, "rb") as file:
        contents = tomli.load(file)
        return Profile(url=contents["url"], file_transfer=None)


@dataclass(frozen=True, slots=True)
class ClientParams:
    """Parameters for creating a client."""

    url: str
    file_transfer: FileTransfer | None


def make_client_params(
    *,
    profile: str | Path | Profile | None,
    url: str | None,
    file_transfer: FileTransfer | None,
) -> ClientParams:
    """Return parameters for creating a client."""
    p = locate_profile(profile) if profile is not None else None
    url = _get_url(p, url)
    file_transfer = _get_file_transfer(p, file_transfer)
    return ClientParams(url=url, file_transfer=file_transfer)


def _get_url(profile: Profile | None, url: str | None) -> str:
    match (profile, url):
        case (None, None):
            raise TypeError("Either `profile` or `url` must be provided")
        case (p, None):
            return p.url  # type: ignore[union-attr]
        case _:
            return url  # type: ignore[return-value]


def _get_file_transfer(
    profile: Profile | None,
    file_transfer: FileTransfer | None,
) -> FileTransfer | None:
    if profile is None:
        return file_transfer
    if file_transfer is None:
        return profile.file_transfer
    return file_transfer
