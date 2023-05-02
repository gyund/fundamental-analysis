import io
import logging
import os
from datetime import date
from pathlib import Path

import mock
import pytest

import ticker.filter as Filter
from tests.fixtures.network.sec import (
    filter_aapl,
    sec_dataselector_2023q1,
    sec_instance,
)
from ticker.cli import Cli
from ticker.data.sec import DataSelector, DataSetReader
from ticker.data.sec import Filter as SecFilter
from ticker.data.sec import ReportDate
from ticker.data.sec import Sec
from ticker.data.sec import Sec as SecDataSource
from ticker.data.sec import TickerReader

logger = logging.getLogger(__name__)


@pytest.mark.webtest
class TestDownloadManager:
    def test_getTickers(self, sec_instance: Sec):
        tickers = sec_instance.download_manager.getTickers()
        assert tickers.getCik("AAPL") == 320193
        assert tickers.getCik("aapl") == 320193
        assert tickers.getTicker(320193) == "AAPL"

    def test_benchmark_getTickers(self, sec_instance: Sec, benchmark):
        benchmark(sec_instance.download_manager.getTickers)

    def test_getData(self, sec_dataselector_2023q1: Sec):
        report: DataSelector = sec_dataselector_2023q1

        tags = report.getTags()
        logger.debug(f"tags({len(tags)}): {tags}")
        assert len(tags) > 0
        # TODO: Verify access semantics so we can create a query API on the extracted data
        # aapl =  df[df.adsh == '0000320193-23-000005']
        # assert aapl.empty == False


@pytest.mark.webtest
def test_update(sec_instance: Sec, filter_aapl: Filter.Selectors):
    # pytest.skip(
    #     "skip until we can resolve performance issues with large data sets")
    data_selector = sec_instance.getData(
        tickers=["aapl"], filter=filter_aapl.sec_filter
    )
    assert data_selector.data.empty == False
    logger.debug(f"There are {len(data_selector.data)} records about apple")
    logger.debug(data_selector.data)
    # logger.debug(data_selector.data.to_markdown())

    # There should only be one record based on the filter
    EntityCommonStockSharesOutstanding = data_selector.data.query(
        "cik == 320193 and tag == 'EntityCommonStockSharesOutstanding'"
    )
    eo_series = EntityCommonStockSharesOutstanding.value

    assert len(eo_series) == 1
    assert eo_series[0] == 15821946000
    assert True == len(data_selector.data) == 1


@pytest.mark.webtest
def test_multi_stock_request_over_1year(sec_instance: SecDataSource):
    # Create the filter we'll use to scrape the results
    sec_filter = SecFilter(
        tags=["EarningsPerShareDiluted"],
        years=1,  # Over the past 5 years
        last_report=ReportDate(year=2023, quarter=1),
        only_annual=True,  # We only want the 10-K
    )
    tickers = ["aapl", "msft", "goog", "tmo"]
    data_selector = sec_instance.getData(tickers=tickers, filter=sec_filter)
    logger.debug(data_selector)
    # TODO: assert something
