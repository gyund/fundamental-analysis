from ticker.data.source import Source

import yfinance as yf
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

class YFinance(Source):
    _session = CachedLimiterSession(
        # max 2 requests per 5 seconds
        limiter=Limiter(RequestRate(2, Duration.SECOND*5)),
        bucket_class=MemoryQueueBucket,
        backend=SQLiteCache(db_path="yfinance.sqlite3")
    )

    def __del__(self):
        self.session.close()

    @property
    def session(self):
        return self._session

    def getCashFlowFromOperatingActivities(self, ticker: str) -> int:
        """ Get cash flow from operating activities

        Args:
            ticker (str): ticker symbol

        Returns:
            int: cash flow
        """        
        ticker = yf.Ticker(ticker=ticker, session=self.session)
        return ticker.cashflow
