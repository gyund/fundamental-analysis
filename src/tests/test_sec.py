import io
import logging
from datetime import date
from pathlib import Path

import mock
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
from stocktracer.data.sec import (
    DataSelector,
    DataSetReader,
    ReportDate,
    Sec,
    TickerReader,
)
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


def test_Sec_init():
    with pytest.raises((TypeError, AssertionError)):
        Sec()


def test_benchmark_DataSetReader_processSubText(
    benchmark, filter_aapl: Filter.Selectors, sub_txt_sample
):
    filter_aapl.sec_filter._cik_list = set()
    filter_aapl.sec_filter._cik_list.add(320193)
    benchmark.pedantic(
        DataSetReader._processSubText,
        args=(io.StringIO(sub_txt_sample), filter_aapl.sec_filter),
    )


def test_benchmark_DataSetReader_processNumText(
    benchmark, filter_aapl: Filter.Selectors, sub_txt_sample, data_txt_sample
):
    filter_aapl.sec_filter._cik_list = set()
    filter_aapl.sec_filter._cik_list.add(320193)
    sub_df = DataSetReader._processSubText(
        filepath_or_buffer=io.StringIO(sub_txt_sample), filter=filter_aapl.sec_filter
    )
    benchmark.pedantic(
        DataSetReader._processNumText,
        args=(io.StringIO(data_txt_sample), filter_aapl.sec_filter, sub_df),
    )


def test_DataSetReader_processSubText(filter_aapl: Filter.Selectors, sub_txt_sample):
    # Put AAPL's CIK in the list so it will be filtered
    filter_aapl.sec_filter._cik_list = set()
    filter_aapl.sec_filter._cik_list.add(320193)
    sub_df = DataSetReader._processSubText(
        filepath_or_buffer=io.StringIO(sub_txt_sample), filter=filter_aapl.sec_filter
    )
    logger.debug(f"sub keys: {sub_df.keys()}")
    logger.debug(sub_df)
    assert "0000320193-23-000006" in sub_df.index.get_level_values("adsh")
    assert "0000723125-23-000022" not in sub_df.index.get_level_values("adsh")
    assert "0000004457-23-000026" not in sub_df.index.get_level_values("adsh")


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
        tags = sec_fake_report.getTags()
        assert len(tags) == 1
        assert "EntityCommonStockSharesOutstanding" in tags

    def test_filterByTicker(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._getCik = mock.Mock(return_value=320193)
        df = sec_fake_report.filterByTicker(ticker="AAPL", data=sec_fake_report.data)
        assert df is not None
        assert 1 == len(df)

    def test_select(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._getCik = mock.Mock(return_value=320193)
        df = sec_fake_report.select(ticker="AAPL")
        assert df is not None

    def test_select_and_pivot(self, sec_manufactured_fake_report: DataSelector):
        """Test to figure out how best to orient the table for summarizing data"""
        sec_manufactured_fake_report._getCik = mock.Mock(return_value=320193)
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


def test_reportDate():
    rd = ReportDate(2023, 1)
    assert rd.year == date.today().year
    assert rd.quarter == 1

    try:
        rd = ReportDate(date.today().year + 1, 1)
        pytest.fail("should throw and exception")
    except ValueError as ex:
        pass

    try:
        rd = ReportDate(date.today().year, 0)
        pytest.fail("should throw and exception")
    except ValueError as ex:
        pass

    rd = ReportDate(date.today().year, 4)
    try:
        rd = ReportDate(date.today().year, 5)
        pytest.fail("should throw and exception")
    except ValueError as ex:
        pass


class TestFilter:
    def test_getRequiredReports_default(self):
        filter = Filter.SecFilter(
            tags=["dummy"],
            last_report=ReportDate(year=2022, quarter=4),
        )

        required_reports = filter.getRequiredReports()

        # You might thing 5, but since companies file annual reports in different quarters,
        # we have to look at all the quarters.
        assert len(required_reports) == 21
        assert required_reports[0] == ReportDate(year=2022, quarter=4)
        assert required_reports[1] == ReportDate(year=2022, quarter=3)
        assert required_reports[2] == ReportDate(year=2022, quarter=2)
        assert required_reports[3] == ReportDate(year=2022, quarter=1)
        assert required_reports[4] == ReportDate(year=2021, quarter=4)

    def test_getRequiredReports_quarterly(self):
        filter = Filter.SecFilter(
            tags=["dummy"],
            years=1,
            last_report=ReportDate(year=2022, quarter=4),
            only_annual=False,
        )
        required_reports = filter.getRequiredReports()

        assert len(required_reports) == 5
        assert required_reports[0] == ReportDate(year=2022, quarter=4)
        assert required_reports[1] == ReportDate(year=2022, quarter=3)
        assert required_reports[2] == ReportDate(year=2022, quarter=2)
        assert required_reports[3] == ReportDate(year=2022, quarter=1)
        assert required_reports[4] == ReportDate(year=2021, quarter=4)
