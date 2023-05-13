import logging
import os
from pathlib import Path

import mock
import numpy as np
import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
from stocktracer.data.sec import (
    DataSetReader,
    DownloadManager,
    ReportDate,
    Sec,
    TickerReader,
)
from tests.fixtures.unit import (
    data_txt_sample,
    fake_data_txt_sample,
    fake_sub_txt_sample,
    filter_aapl,
    filter_aapl_years,
    sec_fake_report,
    sec_manufactured_fake_report,
    sec_manufactured_fake_report_impl,
    sub_txt_sample,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def sec_harness() -> tuple[Sec, mock.MagicMock]:
    sec = Sec(Path(os.getcwd()) / ".test-cache")

    # Mock all objects that interact with network elements.
    # You will need to re-mock them in the test to get code completion
    # for setting checks if the mock gets called.
    sec.download_manager = mock.MagicMock(DownloadManager)
    return sec, sec.download_manager


class TestSec:
    def test_init(self):
        with pytest.raises((TypeError, AssertionError)):
            Sec()

    def test_select_data(
        self,
        sec_harness: tuple[Sec, mock.MagicMock],
        fake_sub_txt_sample: str,
        fake_data_txt_sample: str,
    ):
        (sec, download_manager) = sec_harness
        data_reader = mock.MagicMock(DataSetReader)
        data_reader.process_zip = mock.MagicMock(return_value=pd.DataFrame())

        ticker_reader = mock.MagicMock(TickerReader)
        type(download_manager).ticker_reader = mock.PropertyMock(
            return_value=ticker_reader
        )
        download_manager.get_quarterly_report = mock.MagicMock(return_value=data_reader)

        with pytest.raises(
            LookupError, match="No data matching the filter was retrieved"
        ):
            sec.select_data(
                tickers=frozenset(("aapl", "msft")),
                filter=Filter.SecFilter(tags=["test"]),
            )
        ticker_reader.contains.assert_called()
        download_manager.get_quarterly_report.assert_called()
        data_reader.process_zip.assert_called()

        # That's as far s this test goes because it requires download and unzipping and then processing

    def test_select_and_pivot(
        self,
        sec_harness: tuple[Sec, mock.MagicMock],
        fake_sub_txt_sample: str,
        fake_data_txt_sample: str,
    ):
        """
                                                                            ddate  ...  fp
        adsh                 tag                                cik                ...
        0000320193-23-000002 EntityCommonStockSharesOutstanding 320193 2023-01-31  ...  Q1
                            FakeAttributeTag                   320193 2023-01-31  ...  Q1
        0000320193-23-000003 EntityCommonStockSharesOutstanding 320193 2023-01-31  ...  Q2
                            FakeAttributeTag                   320193 2023-01-31  ...  Q2
        0000320193-23-000004 EntityCommonStockSharesOutstanding 320193 2023-01-31  ...  Q3
                            FakeAttributeTag                   320193 2023-01-31  ...  Q3
        0000320193-23-000005 EntityCommonStockSharesOutstanding 320193 2023-01-31  ...  Q4
                            FakeAttributeTag                   320193 2023-01-31  ...  Q4
        0000320193-23-000006 EntityCommonStockSharesOutstanding 320193 2023-01-31  ...  Q1
                            FakeAttributeTag                   320193 2023-01-31  ...  Q1
        """
        (sec, download_manager) = sec_harness
        aapl_filter = filter_aapl_years(1)
        data = sec_manufactured_fake_report_impl(
            aapl_filter, fake_sub_txt_sample, fake_data_txt_sample
        )
        data_reader = mock.MagicMock(DataSetReader)
        data_reader.process_zip = mock.MagicMock(return_value=data)
        download_manager.get_quarterly_report = mock.MagicMock(return_value=data_reader)

        ticker_reader = mock.MagicMock(TickerReader)
        type(download_manager).ticker_reader = mock.PropertyMock(
            return_value=ticker_reader
        )
        ticker_reader._data = pd.read_json(
            """{"0":{"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."},
         "1":{"cik_str":789019,"ticker":"MSFT","title":"MICROSOFT CORP"}}""",
            orient="index",
        )

        filter = sec.select_data(
            tickers=frozenset("aapl"),
            filter=Filter.SecFilter(last_report=ReportDate(2023, 1)),
        )

        logger.debug(f"\n{data}")
        table = pd.pivot_table(
            filter.filtered_data,
            values="value",
            index=["cik", "tag"],
            aggfunc=np.average,
        )
        logger.debug(f"processed:\n{table}")
        assert table.loc[320193].loc["EntityCommonStockSharesOutstanding"][0] == 4000
        assert table.loc[320193].loc["FakeAttributeTag"][0] == 400

        table = filter.select(aggregate_func=np.average)
        logger.debug(f"select_avg:\n{table}")

        assert table.get_value(320193, "EntityCommonStockSharesOutstanding") == 4000
        assert table.get_value(320193, "FakeAttributeTag") == 400

        table = filter.select(aggregate_func=np.average, tickers=["bad"])
        # normally bad tickers throw exceptions, but we'll just have it filter on
        # an index we don't have so we get an empty value
        assert table.data.empty == True

        # Filter on aapl and get only thses results
        table = filter.select(aggregate_func=np.average, tickers=["aapl"])
        assert table.data.empty == False
        logger.debug(f"processed-ticker:\n{table.data}")
        assert table.get_value(320193, "EntityCommonStockSharesOutstanding") == 4000
        # assert table.data.loc[320193].loc["FakeAttributeTag"][0] == 400
        # assert table.data.loc[320193].loc["FakeAttributeTag"][0] == 400
        assert table.get_value(ticker_or_cik="aapl", tag="FakeAttributeTag") == 400
        assert table.get_value(ticker_or_cik=320193, tag="FakeAttributeTag") == 400

        assert (
            filter.select(aggregate_func="max", tickers=["aapl"]).get_value(
                ticker_or_cik=320193, tag="FakeAttributeTag"
            )
            == 600
        )
        assert (
            filter.select(aggregate_func="min", tickers=["aapl"]).get_value(
                ticker_or_cik=320193, tag="FakeAttributeTag"
            )
            == 200
        )
        assert (
            filter.select(aggregate_func="mean", tickers=["aapl"]).get_value(
                ticker_or_cik=320193, tag="FakeAttributeTag"
            )
            == 400
        )
        assert (
            filter.select(aggregate_func="std", tickers=["aapl"]).get_value(
                ticker_or_cik=320193, tag="FakeAttributeTag"
            )
            == 158.11388300841898
        )
        assert (
            filter.select(aggregate_func="sum", tickers=["aapl"]).get_value(
                ticker_or_cik=320193, tag="FakeAttributeTag"
            )
            == 2000
        )
        assert (
            filter.select(aggregate_func="var", tickers=["aapl"]).get_value(
                ticker_or_cik=320193, tag="FakeAttributeTag"
            )
            == 25000
        )
