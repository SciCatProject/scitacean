# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import cache

from ..typing import FileTransfer


@dataclass(frozen=True, slots=True)
class Profile:
    """Parameters for connecting to a specific instance of SciCat.

    The fields of a profile correspond to the arguments of the constructors
    of :class:`Client`.
    They can be overridden by the explicit constructor arguments.

    When constructing a client from a profile, the ``profile`` argument may be one of:

    - If ``profile`` is a :class:`Profile`, it is returned as is.
    - If ``profile`` is a :class:`str`, a builtin profile with that
        name is constructed if possible.
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

    frontend_url: str | None = None
    """URL of the SciCat frontend.

    See :attr:`Profile.url` for more information.
    """


def locate_profile(spec: str | Profile) -> Profile:
    """Find and return a specified profile."""
    if isinstance(spec, Profile):
        return spec
    return _get_builtin_profile(spec)


def gather_login_params(
    *,
    profile: str | Profile | None,
    url: str | None,
    file_transfer: FileTransfer | None,
) -> Profile:
    """Return parameters for creating a client."""
    p = locate_profile(profile) if profile is not None else None
    if p is None:
        if url is None:
            raise TypeError("Either `profile` or `url` must be provided")
        return Profile(url=url, file_transfer=file_transfer)

    return replace(p, url=url or p.url, file_transfer=file_transfer or p.file_transfer)


def _get_url(profile: Profile | None, url: str | None) -> str:
    match (profile, url):
        case (None, None):
            raise TypeError("Either `profile` or `url` must be provided")
        case (p, None):
            return p.url  # type: ignore[union-attr]
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


def _get_builtin_profile(name: str) -> Profile:
    profiles = _builtin_profiles()
    try:
        factory = profiles[name]
    except KeyError:
        raise ValueError(
            f"Unknown profile: '{name}'. Available profiles:\n{', '.join(profiles)}"
        ) from None
    return factory()


@cache
def _builtin_profiles() -> dict[str, Callable[[], Profile]]:
    from ._ess import profiles as ess_profiles

    profile_list = (*ess_profiles,)
    profiles = {}

    for name, profile in profile_list:
        if name in profiles:
            raise RuntimeError(
                f"Duplicate profile name: '{name}'. "
                "This is likely an internal Scitacean error."
            )
        profiles[name] = profile
    return profiles
