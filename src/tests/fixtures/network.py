import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
import stocktracer.collector.sec as Sec
from tests.fixtures.unit import filter_aapl


@pytest.fixture
def sec_dataselector_2023q1(filter_aapl: Filter.Selectors) -> Filter.Selectors:
    Sec.filter_data(
        tickers=filter_aapl.ticker_filter, sec_filter=filter_aapl.sec_filter
    )
    return filter_aapl
