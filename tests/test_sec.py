import pytest
import mock
import os
from ticker.cli import Cli
from ticker.data.sec import Sec, ReportDate, TickerReader, DataSetReader
from datetime import date
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


def test_reportDate():
    rd = ReportDate(2023, 1)
    assert rd.year == date.today().year
    assert rd.quarter == 1

    try:
        rd = ReportDate(date.today().year+1, 1)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass

    try:
        rd = ReportDate(date.today().year, 0)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass

    rd = ReportDate(date.today().year, 4)
    try:
        rd = ReportDate(date.today().year, 5)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass


def test_getDownloadList_1():
    dl_list = Sec._getDownloadList(
        years=1, last_report=ReportDate(year=2022, quarter=4))
    assert len(dl_list) == 5
    assert dl_list[0] == ReportDate(year=2022, quarter=4)
    assert dl_list[1] == ReportDate(year=2022, quarter=3)
    assert dl_list[2] == ReportDate(year=2022, quarter=2)
    assert dl_list[3] == ReportDate(year=2022, quarter=1)
    assert dl_list[4] == ReportDate(year=2021, quarter=4)


class TestSecHarness:
    # test using the real SEC adapter
    sec = Sec(Path(os.path.dirname(os.path.realpath(__file__))) / ".ticker-cache")

    @pytest.mark.skipif(os.getenv("TICKER_TEST_SEC") is None,
                        reason="env variable TICKER_TEST_SEC not set")
    def test_getTickers(self):
        tickers = self.sec.download_manager.getTickers()
        assert tickers.getCik('AAPL') == 320193
        assert tickers.getCik('aapl') == 320193
        assert tickers.getTicker(320193) == 'AAPL'

    @pytest.mark.skipif(os.getenv("TICKER_TEST_SEC") is None,
                        reason="env variable TICKER_TEST_SEC not set")
    def test_getData(self):
        data = self.sec.download_manager.getData(
            ReportDate(year=2023, quarter=1))
        df = data.getData()
        assert df.empty == False
        # TODO: Verify access semantics so we can create a query API on the extracted data
        # aapl =  df[df.adsh == '0000320193-23-000005']
        # assert aapl.empty == False

    @pytest.mark.skipif(os.getenv("TICKER_TEST_SEC") is None,
                        reason="env variable TICKER_TEST_SEC not set")
    def test_update(self):
        df = self.sec.update(tickers=['aapl'], years=1,last_report=ReportDate(year=2023, quarter=1))
        assert df.empty == False
