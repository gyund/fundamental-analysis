import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
from stocktracer.data.sec import DataSelector, Sec
from tests.fixtures.unit import filter_aapl


@pytest.fixture
def sec_instance() -> Sec:
    # test using the real SEC adapter
    return Sec(Cli._getDefaultCachePath())


@pytest.fixture
def sec_dataselector_2023q1(
    sec_instance: Sec, filter_aapl: Filter.Selectors
) -> DataSelector:
    return sec_instance.getData(
        tickers=filter_aapl.ticker_filter, filter=filter_aapl.sec_filter
    )
