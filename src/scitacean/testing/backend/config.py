# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Backend configuration."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict


class ScicatCredentials(TypedDict):
    """A dict with testing credentials for SciCat."""

    username: str
    password: str


@dataclass
class ScicatUser:
    """A SciCat user.

    Warning
    -------
    Only ever use this for testing!
    This class does not have the usual protections against
    leaks of secrets used by the client.
    """

    username: str
    password: str
    email: str
    group: str

    @property
    def credentials(self) -> ScicatCredentials:
        """Return login credentials for this user.

        User as

        .. code-block:: python

            client = Client.from_credentials(url="...", **user.credentials)
        """
        return {
            "username": self.username,
            "password": self.password,
        }

    def dump(self) -> dict[str, str | bool]:
        """Return a dict that can be serialized to functionalAccounts.json."""
        return {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "role": self.group,
            "global": False,
        }


# see https://github.com/SciCatProject/scicat-backend-next/blob/master/src/config/configuration.ts
USERS = {
    "ingestor": ScicatUser(
        username="ingestor",
        password="aman",  # noqa: S106
        email="scicatingestor@your.site",
        group="ingestor",
    ),
    "user1": ScicatUser(
        username="user1",
        password="a609316768619f154ef58db4d847b75e",  # noqa: S106
        email="user1@your.site",
        group="group1",
    ),
    "user2": ScicatUser(
        username="user2",
        password="f522d1d715970073a6413474ca0e0f63",  # noqa: S106
        email="user2@your.site",
        group="group2",
    ),
    "user3": ScicatUser(
        username="user3",
        password="70dc489e8ee823ae815e18d664424df2",  # noqa: S106
        email="user3@your.site",
        group="group3",
    ),
    "user4": ScicatUser(
        username="user4",
        password="0014890e7020f515b92b767227ef2dfa",  # noqa: S106
        email="user4@your.site",
        group="group4",
    ),
    "user5.1": ScicatUser(
        username="user5.1",
        password="359a5fda99bfe5dbc42ee9b3ede77fb7",  # noqa: S106
        email="user5.1@your.site",
        group="group5",
    ),
    "user5.2": ScicatUser(
        username="user5.2",
        password="f3ebd2e4def95db59ef95ee32ef45242",  # noqa: S106
        email="user5.2@your.site",
        group="group5",
    ),
}
"""Pre-configured users of the backend."""

SCICAT_PORT = 3000
"""Port of the SciCat server on localhost."""
PID_PREFIX = "PID.prefix.a0b1"
"""Prefix for PIDs that gets inserted by the server."""
SITE = "SCITACEAN"
"""Name of the deployment site (facility) of SciCat."""


@dataclass
class SciCatAccess:
    """Access parameters for a local SciCat backend."""

    url: str
    user: ScicatUser


def local_access(user: str) -> SciCatAccess:
    """Return parameters to connect a client to a local SciCat backend.

    Parameters
    ----------
    user:
        User name.
        Must be in :attr:`scitacean.testing.backend.config.USERS`.

    Returns
    -------
    :
        Parameters for the local SciCat backend.
    """
    return SciCatAccess(url=f"http://localhost:{SCICAT_PORT}/api/v3/", user=USERS[user])


def dump_account_config(path: Path) -> None:
    """Write a functional account config for the backend."""
    with path.open("w") as f:
        json.dump([user.dump() for user in USERS.values()], f)
