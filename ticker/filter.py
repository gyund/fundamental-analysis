from ticker.data.sec import Filter as SecFilter

class Selectors:

    def __init__(self,
                 ticker_filter: set[str] | list[str],
                 sec_filter: SecFilter) -> None:
        """ Entry for data to search for in various sources

        Args:
            ticker_filter (set[str] | list[str],): list of stock tickers to get information about
            sec_filter (SecFilter): filter for SEC reports
        """        
        assert True == isinstance(sec_filter, SecFilter)
        
        self.ticker_filter = set(ticker_filter)
        self.sec_filter = sec_filter
        
 