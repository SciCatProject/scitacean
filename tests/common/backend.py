import json
from pathlib import Path
import requests
import shutil
import subprocess
import time
from urllib.parse import urljoin

from ..data import load_datasets, load_orig_datablocks


_TEST_BASE = Path(__file__).resolve().parent.parent
_SCICAT_DOCKER_CONFIG = _TEST_BASE / "scicatlive/docker-compose.yaml"
_SCICAT_DATASET_SEED_FILE = Path("seed_db/seed/Dataset.json")
_SCICAT_ORIG_DATABLOCK_SEED_FILE = Path("seed_db/seed/OrigDatablock.json")


# List of required services for tests.
# We only need the backend and API to run tests.
_SERVICES = ("catamel", "mongodb", "mongodb_seed", "reverse-proxy")


def can_connect(scicat_access) -> bool:
    response = requests.post(
        urljoin(scicat_access.url, "Users/login"),
        json=scicat_access.functional_credentials,
    )
    return response.ok


def wait_until_backend_is_live(scicat_access, max_time: float, n_tries: int):
    """
    The containers take a while to be fully live.
    """
    for _ in range(n_tries):
        if can_connect(scicat_access):
            return
        time.sleep(max_time / n_tries)
    if not can_connect(scicat_access):
        raise RuntimeError("Cannot connect to backend")


def _merge_seed_file(target_dir, seed_file_name, custom_seed):
    with open(target_dir / seed_file_name, "r") as f:
        dset_seed = json.load(f)
    dset_seed.extend(custom_seed)
    with open(target_dir / seed_file_name, "w") as f:
        json.dump(dset_seed, f)


def configure(target_dir) -> Path:
    target = Path(target_dir) / "scicatlive"
    shutil.copytree(_SCICAT_DOCKER_CONFIG.parent, target)
    _merge_seed_file(target, _SCICAT_DATASET_SEED_FILE, load_datasets())
    _merge_seed_file(target, _SCICAT_ORIG_DATABLOCK_SEED_FILE, load_orig_datablocks())

    return target / _SCICAT_DOCKER_CONFIG.name


def start_backend_containers(config_file):
    # waiting for scicatlive-mongodb_seed-1 with recreate seems to deadlock
    subprocess.check_call(
        [
            "docker",
            "compose",
            "--file",
            config_file,
            "up",
            "--detach",
            "--force-recreate",
            *_SERVICES,
        ]
    )


def stop_backend_containers(config_file):
    subprocess.check_call(
        ["docker", "compose", "--file", config_file, "down", "--volumes"]
    )
