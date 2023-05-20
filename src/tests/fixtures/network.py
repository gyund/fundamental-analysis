import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli, get_default_cache_path
from stocktracer.data.sec import Sec
from tests.fixtures.unit import filter_aapl


@pytest.fixture
def sec_instance() -> Sec:
    # test using the real SEC adapter
    return Sec(get_default_cache_path())


@pytest.fixture
def sec_dataselector_2023q1(
    sec_instance: Sec, filter_aapl: Filter.Selectors
) -> Filter.Selectors:
    sec_instance.filter_data(
        tickers=filter_aapl.ticker_filter, filter=filter_aapl.sec_filter
    )
    return filter_aapl
