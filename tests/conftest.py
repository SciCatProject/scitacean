import pytest

from .common import backend


def pytest_addoption(parser):
    parser.addoption(
        "--backend-tests",
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )


def pytest_collection_modifyitems(config, items):
    # Disable backend tests unless the --backend-tests option is set.
    run_backend_tests = config.getoption("--backend-tests")
    if run_backend_tests:
        return
    skip_backend_tests = pytest.mark.skip(reason="backend test")
    for item in items:
        if "scicat_backend" in item.fixturenames:
            item.add_marker(skip_backend_tests)


@pytest.fixture(scope="module")
def scicat_backend():
    backend.start_backend_containers()
    backend.wait_until_backend_is_live(max_time=20, n_tries=20)
    yield
    backend.stop_backend_containers()
