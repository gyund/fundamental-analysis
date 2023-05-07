import logging
from typing import Optional

import numpy as np
import pandas as pd

from stocktracer.data.sec import Filter as SecFilter
from stocktracer.data.sec import ReportDate
from stocktracer.data.sec import Sec as SecDataSource
from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


def trendline(data: pd.Series, order: int = 1) -> float:
    """Calculate the trend of a series.

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
    """Perform an analysis on the earnings per share over time."""

    def analyze(self) -> Optional[pd.DataFrame]:
        # Create the filter we'll use to scrape the results
        sec_filter = SecFilter(
            tags=["EarningsPerShareDiluted"],
            years=1,  # Over the past 5 years
            last_report=ReportDate(year=2023, quarter=1),
            only_annual=True,  # We only want the 10-K
        )

        # Create an SEC Data Source
        assert self.options is not None
        assert self.options.cache_path is not None
        sec = SecDataSource(storage_path=self.options.cache_path)
        data_selector = sec.select_data(tickers=self.options.tickers, filter=sec_filter)

        # # Show a quick dump of the data
        # logger.info(f"\n{data_selector.data}")

        # # Get only the EPSD Data
        eps_diluted = data_selector.data.query("tag == 'EarningsPerShareDiluted'")
        # TODO: Figure this out
        # return eps_diluted.groupby(["cik"]).apply(lambda x: pd.Series(trendline(x.value),
        #                                                               index=["trend"]))
        return eps_diluted.groupby(["cik"]).all()

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__
