# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from functools import cache
from typing import Any, Literal, TypeAlias

from ..typing import FileTransfer

ScientificMetadataSchema: TypeAlias = Literal["plain", "value-unit"]


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

    scientific_metadata_schema: ScientificMetadataSchema = "plain"
    """The schema used for scientific metadata.

    - "plain": No special handling. The metadata is used as provided by the user.
    - "value-unit": The metadata is expected to be a dictionary
      with keys "value" and "unit".

    This is currently unused by Scitacean.
    """

    field_factories: dict[str, Callable[..., Any]] = field(default_factory=dict)
    """Mapping of field names to functions that compute field values.

    Each item is a pair of field name and a function that computes a value for that
    field from other fields. The function can take any number of arguments.
    When calling a factory the arguments are provided based on the dataset that
    a field is being built for. See the example below.

    Field names can be any dataset field plus the following:

    - ``instrumentNames``: The names of the instruments based
      on instrument IDs if the Ids are known.

    Scitacean itself does not currently use this field.
    It is only used by the Scitacean widget.

    Note
    ----
    All field names use the SciCat names (see
    `Models <../../user-guide/classes-and-concepts.rst#models>`_) instead of the
    names used in :class:`scitacean.Dataset`.
    That is, e.g., ``proposalIds`` instead of ``proposal_ids`` or ``sourceFolder``
    instead of ``source_folder``.

    Examples
    --------
    Use the proposal ID of a dataset to construct the owner group:

        >>> field_factories = {
        ...     "ownerGroup": lambda proposalId: str(proposalIds[0]).strip(),
        ... }

    Using ``str()`` and ``strip()`` here is just a cautionary measure, typically,
    the proposal ID should already be a stripped string.
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
