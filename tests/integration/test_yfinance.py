import pytest
import os
import yfinance as yf
import logging

from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

log = logging.getLogger(__name__)


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


@pytest.mark.skipif(os.getenv("SFA_INTEGRATION") is None, 
                    reason="env variable SFA_INTEGRATION not set")
def test_call_yfinance():
    session = CachedLimiterSession(
        # max 2 requests per 5 seconds
        limiter=Limiter(RequestRate(2, Duration.SECOND*5)),
        bucket_class=MemoryQueueBucket,
        backend=SQLiteCache("yfinance.sqlite3")
    )

    tickers = yf.Tickers(tickers='msft aapl goog', session=session)

    # access each ticker using (example)
    log.debug(tickers.tickers['MSFT'].info)
    log.debug(tickers.tickers['AAPL'].history(period="1mo"))
    log.debug(tickers.tickers['GOOG'].actions)
    session.close()
