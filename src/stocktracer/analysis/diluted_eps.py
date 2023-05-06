import logging

import numpy as np
import pandas as pd

from stocktracer.data.sec import DataSelector as SecDataSelector
from stocktracer.data.sec import Filter as SecFilter
from stocktracer.data.sec import ReportDate
from stocktracer.data.sec import Sec as SecDataSource
from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


def trendline(data: pd.Series, order: int = 1) -> float:
    """Calculate the trend of a series

    >>> trendline(pd.Series((1,2,3)))
    1.0000000000000004

    Args:
        data (pd.Series): _description_
        order (int): _description_. Defaults to 1.

    Returns:
        float: slope of the trend line
    """
    coeffs = np.polyfit(data.index.values, list(data), order)
    slope = coeffs[-2]
    return float(slope)


class Analysis(AnalysisInterface):
    def analyze(self) -> pd.DataFrame:
        """Perform an analysis on the earnings per share over time

        Args:
            options (Options): options to use for processing
        """
        # Create the filter we'll use to scrape the results
        sec_filter = SecFilter(
            tags=["EarningsPerShareDiluted"],
            years=1,  # Over the past 5 years
            last_report=ReportDate(year=2023, quarter=1),
            only_annual=True,  # We only want the 10-K
        )

        # Create an SEC Data Source
        sec = SecDataSource(storage_path=self.options.cache_path)
        data_selector = sec.getData(tickers=self.options.tickers, filter=sec_filter)

        # Show a quick dump of the data
        logger.info(f"\n{data_selector.data}")

        # results = list[tuple[str, int]]
        results = pd.DataFrame(columns=["ticker", "eps_diluted_trend", "units"])
        for t in self.options.tickers:
            ticker_ds = data_selector.select(ticker=t)
            try:
                eps_diluted = ticker_ds.query("tag == 'EarningsPerShareDiluted'")
                trend = trendline(data=eps_diluted)
                results.insert(
                    column={
                        "ticker": [t],
                        "eps_diluted_trend": [trend],
                        "units": "eps/qtr",
                    }
                )
            except AttributeError as ex:
                logger.warning(f"{t}: {ex}")
        results.sort_values(by=["units"])
        print(f"Trends:\n{results}")
        return results
