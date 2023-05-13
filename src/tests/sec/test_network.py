import io
import logging
import os
from datetime import date
from pathlib import Path

import mock
import pytest

import stocktracer.filter as Filter
from stocktracer.data.sec import Filter as SecFilter
from stocktracer.data.sec import ReportDate
from stocktracer.data.sec import Sec
from stocktracer.data.sec import Sec as SecDataSource
from tests.fixtures.network import filter_aapl, sec_dataselector_2023q1, sec_instance

logger = logging.getLogger(__name__)


@pytest.mark.webtest
class TestTickerReader:
    def test_contains(self, sec_instance: Sec):
        ticker_reader = sec_instance.download_manager.ticker_reader
        assert ticker_reader.contains(frozenset(("aapl", "msft")))
        with pytest.raises(LookupError, match="unable to find ticker: invalid"):
            ticker_reader.contains(frozenset(("aapl", "msft", "invalid")))


@pytest.mark.webtest
class TestDownloadManager:
    def test_getTickers(self, sec_instance: Sec):
        ticker_reader = sec_instance.download_manager.ticker_reader
        assert ticker_reader.convert_to_cik("AAPL") == 320193
        assert ticker_reader.convert_to_cik("aapl") == 320193
        assert ticker_reader.convert_to_ticker(320193) == "AAPL"

    def test_getData(self, sec_dataselector_2023q1: Filter.Selectors):
        report: Filter.Selectors = sec_dataselector_2023q1

        tags = report.sec_filter.tags
        logger.debug(f"tags({len(tags)}): {tags}")
        assert len(tags) > 0
        # TODO: Verify access semantics so we can create a query API on the extracted data
        # aapl =  df[df.adsh == '0000320193-23-000005']
        # assert aapl.empty == False


@pytest.mark.webtest
def test_update(sec_instance: Sec, filter_aapl: Filter.Selectors):
    # pytest.skip(
    #     "skip until we can resolve performance issues with large data sets")
    sec_instance.select_data(tickers=frozenset(["aapl"]), filter=filter_aapl.sec_filter)
    assert filter_aapl.sec_filter.filtered_data.empty == False
    logger.debug(
        f"There are {len(filter_aapl.sec_filter.filtered_data)} records about apple"
    )
    logger.debug(filter_aapl.sec_filter.filtered_data)
    # logger.debug(filter_aapl.sec_filter.filtered_data.to_markdown())

    # There should only be one record based on the filter
    EntityCommonStockSharesOutstanding = filter_aapl.sec_filter.filtered_data.query(
        "cik == 320193 and tag == 'EntityCommonStockSharesOutstanding'"
    )
    eo_series = EntityCommonStockSharesOutstanding.value

    assert len(eo_series) == 1
    assert eo_series[0] == 15821946000
    assert True == len(filter_aapl.sec_filter.filtered_data) == 1


@pytest.mark.webtest
def test_multi_stock_request_over_1year(sec_instance: SecDataSource):
    # Create the filter we'll use to scrape the results
    sec_filter = SecFilter(
        tags=["EarningsPerShareDiluted"],
        years=1,  # Over the past 1 year
        last_report=ReportDate(year=2023, quarter=1),
        only_annual=True,  # We only want the 10-K
    )
    tickers = frozenset(["aapl", "msft", "goog", "tmo"])
    sec_instance.select_data(tickers=tickers, filter=sec_filter)
    logger.debug(sec_filter.filtered_data)
    # Get series for data and make sure they're all yearly-focus(YF)/annual reports
    yearly_focus_periods = "FY"
    quarterly_focus_periods = ("Q1", "Q2", "Q3", "Q4")
    assert False == sec_filter.filtered_data.query("fp in @yearly_focus_periods").empty
    qfp_results = sec_filter.filtered_data.query("fp in @quarterly_focus_periods")
    assert True == qfp_results.empty
