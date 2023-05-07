import logging
import os
from datetime import date
from pathlib import Path

import mock
import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
from stocktracer.data.sec import (
    DataSelector,
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
    sec_fake_report,
    sec_manufactured_fake_report,
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

    def test_getData(self, sec_harness: tuple[Sec, mock.MagicMock]):
        (sec, download_manager) = sec_harness
        data_reader = mock.MagicMock(DataSetReader)
        data_reader.processZip = mock.MagicMock(return_value=pd.DataFrame())

        ticker_reader = mock.MagicMock(TickerReader)
        download_manager.getTickers = mock.MagicMock(return_value=ticker_reader)
        download_manager.getData = mock.MagicMock(return_value=data_reader)

        with pytest.raises(
            LookupError, match="No data matching the filter was retrieved"
        ):
            sec.getData(
                tickers=frozenset(("aapl", "msft")),
                filter=Filter.SecFilter(tags=["test"]),
            )
        ticker_reader.contains.assert_called()
        data_reader.processZip.assert_called()


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
