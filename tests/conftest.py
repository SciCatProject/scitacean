import pytest

from .common import backend


def pytest_addoption(parser):
    parser.addoption(
        "--backend-tests",
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )


@pytest.fixture(scope="module")
def scicat_backend(request):
    """Spin up a SciCat backend and API.

    Does nothing unless the --backend-tests command line option is set.
    """

    if request.config.getoption("--backend-tests"):
        backend.start_backend_containers()
        backend.wait_until_backend_is_live(max_time=20, n_tries=20)
        yield True
        backend.stop_backend_containers()
    else:
        yield False


@pytest.fixture
def scicat_url():
    return "http://localhost:80/api/v3"


@pytest.fixture
def functional_credentials():
    return {"username": "ingestor", "password": "aman"}
