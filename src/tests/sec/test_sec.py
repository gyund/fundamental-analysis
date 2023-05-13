import logging
import os

from pathlib import Path

import mock
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

    def test_select_data(self, sec_harness: tuple[Sec, mock.MagicMock]):
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

