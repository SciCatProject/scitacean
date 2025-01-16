# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Profiles for connecting to SciCat."""

from dataclasses import dataclass
from pathlib import Path

import tomli

from .typing import FileTransfer


@dataclass(frozen=True, slots=True)
class Profile:
    url: str
    file_transfer: FileTransfer | None


def locate_profile(spec: str | Path | Profile) -> Profile:
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
            return Profile(url="https://scicat.ess.eu/api/v3", file_transfer=None)
        case "staging.ess":
            return Profile(
                url="https://staging.scicat.ess.eu/api/v3", file_transfer=None
            )
    raise KeyError(f"Unknown builtin profile: {name}")


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
    profile: str | Profile | None,
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
            return p.url
        case _:
            return url


def _get_file_transfer(
    profile: Profile | None,
    file_transfer: FileTransfer | None,
) -> FileTransfer | None:
    if profile is None:
        return file_transfer
    if file_transfer is None:
        return profile.file_transfer
    return file_transfer
