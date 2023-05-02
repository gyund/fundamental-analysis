import logging

import numpy as np
import pandas as pd

from ticker.cli import Options, ReportOptions
from ticker.data.sec import DataSelector as SecDataSelector
from ticker.data.sec import Filter as SecFilter
from ticker.data.sec import ReportDate
from ticker.data.sec import Sec as SecDataSource

logger = logging.getLogger(__name__)


def trendline(data: pd.Series, order: int = 1) -> float:
    """Calculate the trend of a series

    >>> trendline((1,2,3))
    1

    Args:
        data (pd.Series): _description_
        order (int): _description_. Defaults to 1.

    Returns:
        float: slope of the trend line
    """
    coeffs = np.polyfit(data.index.values, list(data), order)
    slope = coeffs[-2]
    return float(slope)


def analyze(options: Options) -> None:
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
    sec = SecDataSource(storage_path=options.cache_path)
    data_selector = sec.getData(tickers=options.tickers, filter=sec_filter)

    # Show a quick dump of the data
    logger.info(f"\n{data_selector.data}")

    results = list[tuple[str, int]]
    for t in options.tickers:
        ticker_ds = data_selector.select(ticker=t)
        eps_diluted = ticker_ds.EarningsPerShareDiluted
        trend = trendline(data=eps_diluted)
        results.append((t, trend))

    print(f"Trends:\n{results}")


def report(options: ReportOptions) -> None:
    """Generate a report

    As a stub, this does nothing, but normally it provides a mechanism
    to customize the report generated from the analysis phase.

    This allows you to keep processed data in a intermediary format and create reports from
    already processed data without having to do it again.

    Args:
        options (ReportOptions): Reporting options to use for processing
    """
    print("This is where we would report our findings, but we're not right now")
