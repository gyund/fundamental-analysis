import pytest
from ticker.cli import Cli
from ticker.data.sec import Sec, ReportDate, DataSelector
import ticker.filter as Filter
import pandas as pd


@pytest.fixture
def sec_instance() -> Sec:
    # test using the real SEC adapter
    return Sec(Cli.getDefaultCachePath())


@pytest.fixture
def filter_aapl() -> Filter.Selectors:
    return Filter.Selectors(
        ticker_filter={"aapl"},
        sec_filter=Filter.SecFilter(
            tags=["EntityCommonStockSharesOutstanding"],
            years=0,  # Just want the current
            last_report=ReportDate(year=2023, quarter=1),
            only_annual=False,
        ),  # We want the 10-Q
    )


@pytest.fixture
def sec_dataselector_2023q1(
    sec_instance: Sec, filter_aapl: Filter.Selectors
) -> DataSelector:
    return sec_instance.getData(
        tickers=filter_aapl.ticker_filter, filter=filter_aapl.sec_filter
    )
