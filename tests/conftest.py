from dataclasses import dataclass
import pytest
import tempfile
from typing import Dict

from .common import backend


def pytest_addoption(parser):
    parser.addoption(
        "--backend-tests",
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )


@pytest.fixture(scope="module")
def scicat_backend(request, scicat_access):
    """Spin up a SciCat backend and API.

    Does nothing unless the --backend-tests command line option is set.
    """

    if request.config.getoption("--backend-tests"):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = backend.configure(temp_dir)
            try:
                backend.start_backend_containers(config_file)
                backend.wait_until_backend_is_live(
                    scicat_access, max_time=20, n_tries=20
                )
                yield True
            finally:
                backend.stop_backend_containers(config_file)
    else:
        yield False


@dataclass
class SciCatAccess:
    url: str
    functional_credentials: Dict[str, str]


@pytest.fixture(scope="module")
def scicat_access():
    return SciCatAccess(
        url="http://localhost/api/v3/",
        functional_credentials={"username": "ingestor", "password": "aman"},
    )
