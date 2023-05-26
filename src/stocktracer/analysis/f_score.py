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

        table = create_normalized_sec_table(sec_filter, self.options, False)
        table.data.fillna(0, inplace=True)

        assert (
            self.options.last_report.year + 1
            not in table.data.index.get_level_values(1)
        )

        logger.debug(f"filtered_data:\n{table.data}")
        max_year = int(table.data.index.get_level_values("fy").max())

        # Do calculations
        table.calculate_return_on_assets("ROA")
        table.calculate_net_income("net-income")
        table.calculate_delta(column_name="delta-ROA", delta_of="ROA")
        table.calculate_debt_to_assets("debt-to-assets")

        # fscore = pd.DataFrame(index=table.data.index)
        # logger.debug(f"\n{fscore}")

        f_score_tags = []

        # - Profitability
        #     - Return on Assets (ROA) (1 point if it is positive in the current year, 0 otherwise);
        table.data["ROA>0"] = (table.data["ROA"] > 0).astype(int)
        f_score_tags.append("ROA>0")
        # TODO: select last year by ROA and assign a 1 if it's positive
        # logger.debug(f"\n{fscore}")

        #     - Operating Cash Flow (1 point if it is positive in the current year, 0 otherwise);

        table.data["NetIncome>0"] = (table.data["net-income"] > 0).astype(int)
        f_score_tags.append("NetIncome>0")
        #     - Change in Return of Assets (ROA) (1 point if ROA is higher in the current year compared to the previous one, 0 otherwise);
        table.data["delta-ROA>0"] = (table.data["delta-ROA"] > 0).astype(int)
        f_score_tags.append("delta-ROA>0")
        #     - Accruals (1 point if Operating Cash Flow/Total Assets is higher than ROA in the current year, 0 otherwise);
        table.data["accruals"] = (
            table.data["OperatingIncomeLoss"] / table.data["Assets"]
        )
        table.data["CF/Total-Assets>ROA"] = (
            table.data["accruals"] > table.data["ROA"]
        ).astype(int)
        f_score_tags.append("CF/Total-Assets>ROA")
        # - Leverage, Liquidity and Source of Funds
        #     - Change in Leverage (long-term) ratio (1 point if the ratio is lower this year compared to the previous one, 0 otherwise);
        table.calculate_delta("debt-to-assets-delta", delta_of="debt-to-assets")
        table.data["debt-to-assets<last-year"] = (
            table.data["debt-to-assets-delta"] < 0
        ).astype(int)
        f_score_tags.append("debt-to-assets<last-year")

        #     - Change in Current ratio (1 point if it is higher in the current year compared to the previous one, 0 otherwise);
        table.data["current-ratio"] = (
            table.data["AssetsCurrent"] / table.data["LiabilitiesCurrent"]
        )
        #     - Change in the number of shares (1 point if no new shares were issued during the last year);
        # - Operating Efficiency
        #     - Change in Gross Margin (1 point if it is higher in the current year compared to the previous one, 0 otherwise);
        #     - Change in Asset Turnover ratio (1 point if it is higher in the current year compared to the previous one, 0 otherwise);

        # f_score.pivot_table(index=['ticker'], columns=['fy','OperatingIncomeLoss'])
        # logger.debug(f"f_score:\n{f_score}")
        # logger.debug(f"{f_score.loc['AAPL']}")
        # logger.debug(f"{f_score.loc['AAPL'].loc[2022]}")
        # logger.debug(f"{f_score.loc['AAPL'].loc[2022]['ROA']}")
        assert math.isclose(
            table.data.loc["AAPL"].loc[2022]["ROA"], 0.2791437, rel_tol=0.00001
        )
        assert math.isclose(
            table.data.loc["AAPL"].loc[2022]["OperatingIncomeLoss"],
            9.822467e10,
            rel_tol=0.00001,
        )
        logger.debug(f"ROA:\n{table.data['ROA']}")
        logger.debug(f"delta ROA:\n{table.data['delta-ROA']}")
        assert math.isclose(
            table.data.loc["AAPL"].loc[2022]["delta-ROA"], 0.042891, rel_tol=0.00001
        )
        return table.slice(year=max_year, tags=f_score_tags)

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__
