"""Piotroski F-score is a number between 0 and 9 which is used to assess strength of company's financial position."""
import logging
import math
from typing import Optional

import pandas as pd
from beartype import beartype

from stocktracer.analysis.annual_reports import create_normalized_sec_table
from stocktracer.data.sec import Filter as SecFilter
from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


@beartype
class Analysis(AnalysisInterface):
    """

    The score is used by financial investors in order to find the best value
    stocks (nine being the best). The score is named after Stanford accounting professor Joseph Piotroski.

    Calculation procedure
    =====================

    The score is calculated based on 9 criteria divided into 3 groups.[2]

    - Profitability
        - Return on Assets (ROA) (1 point if it is positive in the current year, 0 otherwise);
        - Operating Cash Flow (1 point if it is positive in the current year, 0 otherwise);
        - Change in Return of Assets (ROA) (1 point if ROA is higher in the current year compared to the previous one, 0 otherwise);
        - Accruals (1 point if Operating Cash Flow/Total Assets is higher than ROA in the current year, 0 otherwise);
    - Leverage, Liquidity and Source of Funds
        - Change in Leverage (long-term) ratio (1 point if the ratio is lower this year compared to the previous one, 0 otherwise);
        - Change in Current ratio (1 point if it is higher in the current year compared to the previous one, 0 otherwise);
        - Change in the number of shares (1 point if no new shares were issued during the last year);
    - Operating Efficiency
        - Change in Gross Margin (1 point if it is higher in the current year compared to the previous one, 0 otherwise);
        - Change in Asset Turnover ratio (1 point if it is higher in the current year compared to the previous one, 0 otherwise);

    Some adjustments that were done in calculation of the required financial ratios are discussed in the original paper.[2]

    The score is calculated based on the data from financial statement of a company. A company gets 1 point for each met criterion. Summing up of all achieved points gives Piotroski F-score (number between 0 and 9).
    """

    under_development = True
    years_of_analysis = 2

    def analyze(self) -> Optional[pd.DataFrame]:
        # Create the filter we'll use to scrape the results
        sec_filter = SecFilter(
            # tags=["EarningsPerShareDiluted"],
            years=self.years_of_analysis,
            last_report=self.options.last_report,
            only_annual=True,  # We only want the 10-K
        )

        table = create_normalized_sec_table(sec_filter, self.options)

        assert (
            self.options.last_report.year + 1
            not in table.data.index.get_level_values(1)
        )

        logger.debug(f"filtered_data:\n{table.data}")

        f_score = pd.DataFrame(
            table.data["OperatingIncomeLoss"].div(table.data["Assets"]), columns=["ROA"]
        )
        f_score = f_score.join(table.data["OperatingIncomeLoss"])
        f_score["delta-ROA"] = f_score.groupby(by=["ticker"]).diff()[
            "OperatingIncomeLoss"
        ]
        # f_score.pivot_table(index=['ticker'], columns=['fy','OperatingIncomeLoss'])
        logger.debug(f"f_score:\n{f_score}")
        # logger.debug(f"{f_score.loc['AAPL']}")
        # logger.debug(f"{f_score.loc['AAPL'].loc[2022]}")
        # logger.debug(f"{f_score.loc['AAPL'].loc[2022]['ROA']}")
        assert math.isclose(
            f_score.loc["AAPL"].loc[2022]["ROA"], 0.2791437, rel_tol=0.00001
        )
        assert math.isclose(
            f_score.loc["AAPL"].loc[2022]["OperatingIncomeLoss"],
            9.822467e10,
            rel_tol=0.00001,
        )
        assert math.isclose(
            f_score.loc["AAPL"].loc[2022]["delta-ROA"], 1.850233e10, rel_tol=0.00001
        )
        return f_score

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__
