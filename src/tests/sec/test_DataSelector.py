import logging

import mock
import numpy as np
import pandas as pd

from stocktracer.data.sec import DataSelector, TickerReader
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


class TestDataSelector:
    def test_verifyIndexes(self, sec_fake_report: DataSelector):
        logger.debug(f"num keys: {sec_fake_report.data.keys()}")
        logger.debug(sec_fake_report.data)
        assert "0000320193-23-000006" in sec_fake_report.data.index.get_level_values(
            "adsh"
        )
        assert (
            "0000723125-23-000022"
            not in sec_fake_report.data.index.get_level_values("adsh")
        )
        logger.debug(f"keys in data: {sec_fake_report.data.keys()}")
        assert "value" in sec_fake_report.data.keys()
        logger.debug(f"index for cik: {sec_fake_report.data.index.names}")

        assert "adsh" in sec_fake_report.data.index.names
        assert "tag" in sec_fake_report.data.index.names
        assert "cik" in sec_fake_report.data.index.names

    def test_getTags(self, sec_manufactured_fake_report: DataSelector):
        tags = sec_manufactured_fake_report.tags
        assert len(tags) == 2
        assert "EntityCommonStockSharesOutstanding" in tags
        assert "FakeAttributeTag" in tags

    def test_filterByTicker(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._get_cik = mock.Mock(return_value=320193)
        df = sec_fake_report.filterByTicker(ticker="AAPL", data=sec_fake_report.data)
        assert df is not None
        assert 1 == len(df)

    def test_select(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._get_cik = mock.Mock(return_value=320193)
        df = sec_fake_report.select(tickers=["AAPL"])
        assert df is not None
        logger.debug(df)

    def test_select_and_pivot(
        self, fake_sub_txt_sample: str, fake_data_txt_sample: str
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
        aapl_filter = filter_aapl_years(1)
        data_selector = sec_manufactured_fake_report_impl(
            aapl_filter, fake_sub_txt_sample, fake_data_txt_sample
        )
        logger.debug(f"\n{data_selector.data}")
        table = pd.pivot_table(
            data_selector.data, values="value", index=["cik", "tag"], aggfunc=np.average
        )
        logger.debug(f"processed:\n{table}")
        assert table.loc[320193].loc["EntityCommonStockSharesOutstanding"][0] == 4000
        assert table.loc[320193].loc["FakeAttributeTag"][0] == 400

        table = data_selector.select(aggregate_func=np.average)
        assert (
            table.data.loc[320193].loc["EntityCommonStockSharesOutstanding"][0] == 4000
        )
        assert table.data.loc[320193].loc["FakeAttributeTag"][0] == 400

        data_selector._ticker_reader = mock.MagicMock(TickerReader)
        data_selector._ticker_reader.convert_to_cik = mock.Mock(return_value=12345)
        table = data_selector.select(aggregate_func=np.average, tickers=["bad"])
        # normally bad tickers throw exceptions, but we'll just have it filter on
        # an index we don't have so we get an empty value
        assert table.data.empty == True

        # Filter on aapl and get only thses results
        # data_selector._ticker_reader = mock.MagicMock(TickerReader)
        data_selector._ticker_reader.convert_to_cik = mock.Mock(return_value=320193)
        table = data_selector.select(aggregate_func=np.average, tickers=["aapl"])
        logger.debug(f"processed-ticker:\n{table.data}")
        assert (
            table.data.loc[320193].loc["EntityCommonStockSharesOutstanding"][0] == 4000
        )
        assert table.data.loc[320193].loc["FakeAttributeTag"][0] == 400
        assert table.data.loc[320193].loc["FakeAttributeTag"][0] == 400
        assert table.getValue(ticker_or_cik="aapl", tag="FakeAttributeTag") == 400
        assert table.getValue(ticker_or_cik=320193, tag="FakeAttributeTag") == 400

        assert data_selector.select(aggregate_func="max", tickers=["aapl"]).getValue(ticker_or_cik=320193, tag="FakeAttributeTag") == 600
        assert data_selector.select(aggregate_func="min", tickers=["aapl"]).getValue(ticker_or_cik=320193, tag="FakeAttributeTag") == 200
        assert data_selector.select(aggregate_func="mean", tickers=["aapl"]).getValue(ticker_or_cik=320193, tag="FakeAttributeTag") == 400
        assert data_selector.select(aggregate_func="std", tickers=["aapl"]).getValue(ticker_or_cik=320193, tag="FakeAttributeTag") == 158.11388300841898
        assert data_selector.select(aggregate_func="sum", tickers=["aapl"]).getValue(ticker_or_cik=320193, tag="FakeAttributeTag") == 2000
        assert data_selector.select(aggregate_func="var", tickers=["aapl"]).getValue(ticker_or_cik=320193, tag="FakeAttributeTag") == 25000
