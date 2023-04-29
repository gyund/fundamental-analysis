import pytest
import mock
import os
import io
from tests.fixtures.network.sec import sec_instance, sec_dataselector_2023q1
from ticker.cli import Cli
from ticker.data.sec import Sec, ReportDate, TickerReader, DataSetReader, DataSelector
from datetime import date
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

if os.getenv("TICKER_TEST_SEC") is None:
    pytest.skip(reason="env variable TICKER_TEST_SEC not set",
                allow_module_level=True)


def test_DownloadManager_getTickers(sec_instance: Sec):
    tickers = sec_instance.download_manager.getTickers()
    assert tickers.getCik('AAPL') == 320193
    assert tickers.getCik('aapl') == 320193
    assert tickers.getTicker(320193) == 'AAPL'


def test_DownloadManager_getData(sec_dataselector_2023q1: Sec):
    report = sec_dataselector_2023q1

    tags = report.getTags()
    logger.debug(f'tags({len(tags)}): {tags}')
    assert len(tags) > 0
    # TODO: Verify access semantics so we can create a query API on the extracted data
    # aapl =  df[df.adsh == '0000320193-23-000005']
    # assert aapl.empty == False


def test_update(sec_instance: Sec):
    pytest.skip("skip until getData is verified")
    df = sec_instance.update(
        tickers=['aapl'], years=1, last_report=ReportDate(year=2023, quarter=1))
    assert df.empty == False
    assert 'adsh' in df.keys()
    assert 'cik' in df.keys()
