import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--run-webtest",
        action="store_true",
        default=False,
        help="Run network based tests",
    )

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-webtest"):
        skipper = pytest.mark.skip(reason="Only run when --run-webtest is given")
        for item in items:
            if "webtest" in item.keywords:
                item.add_marker(skipper)