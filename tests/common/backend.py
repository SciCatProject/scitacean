# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import json
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union
from urllib.parse import urljoin

import pytest
import requests

from ..data import load_datasets, load_orig_datablocks
from .docker import docker_compose

_TEST_BASE = Path(__file__).resolve().parent.parent
_SCICAT_DOCKER_CONFIG = _TEST_BASE / "scicatlive/docker-compose.yaml"
_SCICAT_DATASET_SEED_FILE = Path("seed_db/seed/Dataset.json")
_SCICAT_ORIG_DATABLOCK_SEED_FILE = Path("seed_db/seed/OrigDatablock.json")


# List of required services for tests.
# We only need the backend and API to run tests.
_SERVICES = ("catamel", "mongodb", "mongodb_seed", "reverse-proxy")


@dataclass
class SciCatAccess:
    url: str
    functional_credentials: Dict[str, str]


@pytest.fixture(scope="session")
def scicat_access():
    return SciCatAccess(
        url="http://localhost/api/v3/",
        functional_credentials={"username": "ingestor", "password": "aman"},
    )


@pytest.fixture(scope="session")
def scicat_backend(request, scicat_access):
    """Spin up a SciCat backend and API.

    Does nothing unless the --backend-tests command line option is set.
    """
    if not request.config.getoption("--backend-tests"):
        yield False
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = configure(temp_dir)
        with docker_compose(config_file, *_SERVICES):
            wait_until_backend_is_live(scicat_access, max_time=20, n_tries=20)
            yield True


def can_connect(scicat_access: SciCatAccess) -> bool:
    response = requests.post(
        urljoin(scicat_access.url, "Users/login"),
        json=scicat_access.functional_credentials,
        timeout=0.5,
    )
    return response.ok


def wait_until_backend_is_live(
    scicat_access: SciCatAccess, max_time: float, n_tries: int
):
    """The containers take a while to be fully live."""
    for _ in range(n_tries):
        if can_connect(scicat_access):
            return
        time.sleep(max_time / n_tries)
    if not can_connect(scicat_access):
        raise RuntimeError("Cannot connect to backend")


def _merge_seed_file(
    target_dir: Path, seed_file_name: Union[str, Path], custom_seed: Union[list, dict]
):
    with open(target_dir / seed_file_name, "r") as f:
        dset_seed = json.load(f)
    dset_seed.extend(custom_seed)
    with open(target_dir / seed_file_name, "w") as f:
        json.dump(dset_seed, f)


def configure(target_dir: Path) -> Path:
    target = Path(target_dir) / "scicatlive"
    shutil.copytree(
        _SCICAT_DOCKER_CONFIG.parent, target, ignore=shutil.ignore_patterns(".git")
    )
    _merge_seed_file(target, _SCICAT_DATASET_SEED_FILE, load_datasets())
    _merge_seed_file(target, _SCICAT_ORIG_DATABLOCK_SEED_FILE, load_orig_datablocks())

    return target / _SCICAT_DOCKER_CONFIG.name


def skip_if_not_backend(request):
    if not request.config.getoption("--backend-tests"):
        # The backend only exists if this option is set.
        pytest.skip(
            "Tests against a real backend are disabled, "
            "use --backend-tests to enable them"
        )
