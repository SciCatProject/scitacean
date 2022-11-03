from pathlib import Path
import requests
import subprocess
import time
from urllib.parse import urljoin, quote_plus

import pytest

_SCICAT_DOCKER_CONFIG = (
    Path(__file__).resolve().parent.parent / "scicatlive/docker-compose.yaml"
)

# List of required services for tests.
# We only need the backend and API to run tests.
_SERVICES = ("catamel", "mongodb", "mongodb_seed", "reverse-proxy")


def can_connect():
    # TODO better endpoint? maybe login?
    pid = "PID.SAMPLE.PREFIX/desy_ds1"
    url = urljoin("http://localhost/api/v3/Datasets/", quote_plus(pid))
    response = requests.get(url)
    return response.ok


def wait_until_backend_is_live(max_time: float, n_tries: int):
    """
    The containers take a while to be fully live.
    """
    for _ in range(n_tries):
        if can_connect():
            return
        time.sleep(max_time / n_tries)
    if not can_connect():
        raise RuntimeError("Cannot connect to backend")


def start_backend_containers():
    # waiting for scicatlive-mongodb_seed-1 with recreate seems to deadlock
    subprocess.check_call(
        [
            "docker",
            "compose",
            "--file",
            _SCICAT_DOCKER_CONFIG,
            "up",
            "--detach",
            "--force-recreate",
            *_SERVICES,
        ]
    )


def stop_backend_containers():
    subprocess.check_call(
        ["docker", "compose", "--file", _SCICAT_DOCKER_CONFIG, "down", "--volumes"]
    )


@pytest.fixture(scope="module")
def scicat_backend():
    start_backend_containers()
    wait_until_backend_is_live(max_time=20, n_tries=20)
    yield
    stop_backend_containers()
