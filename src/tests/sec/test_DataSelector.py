import logging

import mock

from stocktracer.data.sec import DataSelector
from tests.fixtures.unit import (
    data_txt_sample,
    fake_data_txt_sample,
    fake_sub_txt_sample,
    filter_aapl,
    sec_fake_report,
    sec_manufactured_fake_report,
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

    def test_getTags(self, sec_fake_report: DataSelector):
        tags = sec_fake_report.tags
        assert len(tags) == 1
        assert "EntityCommonStockSharesOutstanding" in tags

    def test_filterByTicker(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._get_cik = mock.Mock(return_value=320193)
        df = sec_fake_report.filterByTicker(ticker="AAPL", data=sec_fake_report.data)
        assert df is not None
        assert 1 == len(df)

    def test_select(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._get_cik = mock.Mock(return_value=320193)
        df = sec_fake_report.select(ticker="AAPL")
        assert df is not None

    def test_select_and_pivot(self, sec_manufactured_fake_report: DataSelector):
        """Test to figure out how best to orient the table for summarizing data"""
        sec_manufactured_fake_report._get_cik = mock.Mock(return_value=320193)
        df = sec_manufactured_fake_report.select(ticker="AAPL")
        df = df[["value"]]
        tag_group = df.groupby(["cik", "tag"])
        average = tag_group.mean()
        logger.debug(average)
        # Should only contain the first entry because the filter specifies 0
        assert (
            False
            == average.query(
                "cik==320193 and tag=='EntityCommonStockSharesOutstanding' and value==6000"
            ).empty
        )
