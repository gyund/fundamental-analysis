import pytest
import os
import yfinance as yf
import logging

from ticker.data.yfinance import YFinance as YFDataSource

log = logging.getLogger(__name__)


class TestYFinanceHarness:
    yfsource = YFDataSource()
    default_ticker = "msft"

    @pytest.mark.skipif(os.getenv("SFA_INTEGRATION") is None,
                        reason="env variable SFA_INTEGRATION not set")
    def test_call_yfinance(self):

        tickers = yf.Tickers(tickers='msft aapl goog',
                             session=self.yfsource.session)

        # access each ticker using (example)
        log.debug(tickers.tickers['MSFT'].info)
        log.debug(tickers.tickers['AAPL'].history(period="1mo"))
        log.debug(tickers.tickers['GOOG'].actions)

    @pytest.mark.skipif(os.getenv("SFA_INTEGRATION") is None,
                        reason="env variable SFA_INTEGRATION not set")
    def test_adapter_calls(self):
        assert True == isinstance(self.yfsource.getCashFlowFromOperatingActivities(
            ticker=self.default_ticker), int)
