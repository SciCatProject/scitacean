# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from dataclasses import dataclass
from typing import Dict


@dataclass
class SciCatUser:
    """Only for testing."""

    username: str
    password: str
    email: str
    group: str

    @property
    def credentials(self) -> Dict[str, str]:
        return {
            "username": self.username,
            "password": self.password,
        }


# see https://github.com/SciCatProject/scicat-backend-next/blob/master/src/config/configuration.ts
USERS = {
    "ingestor": SciCatUser(
        username="ingestor",
        password="aman",  # noqa: S106
        email="scicatingestor@your.site",
        group="ingestor",
    ),
    "user1": SciCatUser(
        username="user1",
        password="a609316768619f154ef58db4d847b75e",  # noqa: S106
        email="user1@your.site",
        group="group1",
    ),
    "user2": SciCatUser(
        username="user2",
        password="f522d1d715970073a6413474ca0e0f63",  # noqa: S106
        email="user2@your.site",
        group="group2",
    ),
    "user3": SciCatUser(
        username="user3",
        password="70dc489e8ee823ae815e18d664424df2",  # noqa: S106
        email="user3@your.site",
        group="group3",
    ),
    "user4": SciCatUser(
        username="user4",
        password="0014890e7020f515b92b767227ef2dfa",  # noqa: S106
        email="user4@your.site",
        group="group4",
    ),
    "user5.1": SciCatUser(
        username="user5.1",
        password="359a5fda99bfe5dbc42ee9b3ede77fb7",  # noqa: S106
        email="user5.1@your.site",
        group="group5",
    ),
    "user5.2": SciCatUser(
        username="user5.2",
        password="f3ebd2e4def95db59ef95ee32ef45242",  # noqa: S106
        email="user5.2@your.site",
        group="group5",
    ),
}

SCICAT_PORT = 3000
PID_PREFIX = "PID.prefix.a0b1"
SITE = "SCITACEAN"


@dataclass
class SciCatAccess:
    url: str
    user: SciCatUser


def local_access(user: str) -> SciCatAccess:
    return SciCatAccess(url=f"http://localhost:{SCICAT_PORT}/api/v3/", user=USERS[user])
