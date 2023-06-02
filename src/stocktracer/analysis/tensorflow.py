"""Use tensorflow to perform automated analysis on stock tickers."""
import logging
from typing import Optional

import pandas as pd

# Load TF-DF
import tensorflow_decision_forests as tfdf
from beartype import beartype

from stocktracer import cache
from stocktracer.analysis.annual_reports import create_normalized_sec_table
from stocktracer.collector.sec import Filter as SecFilter
from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


@beartype
class Analysis(AnalysisInterface):
    """Class for collecting and processing annual report data."""

    under_development = True

    def analyze(self) -> Optional[pd.DataFrame]:
        # Build a training set involving good companies
        sec_filter = SecFilter(
            tags={
                "EarningsPerShareDiluted",
                "CommonStockSharesIssued",
                "AssetsCurrent",
                "LiabilitiesCurrent",
                "Assets",
                "OperatingIncomeLoss",
                "NetCashProvidedByUsedInOperatingActivities",
            },
            years=5,  # Over the past 5 years
            last_report=self.options.final_report,
            only_annual=True,  # We only want the 10-K
        )

        good_tickers = set()
        good_tickers.add("aapl")
        good_tickers.add("msft")
        good_tickers.add("goog")
        good_tickers.add("hd")
        good_tickers.add("acn")
        good_tickers.add("nvda")

        bad_tickers = set()
        bad_tickers.add("wdc")
        bad_tickers.add("nclh")
        bad_tickers.add("grpn")
        bad_tickers.add("capr")
        combined_tickers = list(
            good_tickers.union(self.options.tickers).union(bad_tickers)
        )

        # Create an SEC Data Source
        table = create_normalized_sec_table(sec_filter, combined_tickers, False)

        table.calculate_return_on_assets("ROA")
        table.calculate_net_income("net_income")
        table.calculate_delta(column_name="delta_ROA", delta_of="ROA")
        table.calculate_debt_to_assets("debt_to_assets")
        table.calculate_current_ratio("current_ratio")
        table.data["good_stock"] = False

        for t in good_tickers:
            table.data.loc[t.upper(), ["good_stock"]] = True

        table.data.fillna(0, inplace=True)

        # Select Training Stocks
        train_df = table.slice(ticker=list(good_tickers.union(bad_tickers)))

        logging.debug(
            f"there are {train_df['good_stock'].sum()} good stocks in the training set"
        )
        logging.debug(f"training_data:\n{train_df.to_string()}")

        # Select Assessment Stocks
        test_df = table.slice(
            ticker=list(good_tickers.difference(self.options.tickers))
        )

        train_ds = tfdf.keras.pd_dataframe_to_tf_dataset(train_df, label="good_stock")
        test_ds = tfdf.keras.pd_dataframe_to_tf_dataset(test_df, label="good_stock")

        # Train a Random Forest model.
        model = tfdf.keras.RandomForestModel()
        model.fit(train_ds)

        # Summary of the model structure.
        model.summary()

        # Evaluate the model.
        model.evaluate(test_ds)

        # Export the model to a SavedModel.
        model.save(str(cache.CACHE_DIR / "tf-model"))

        return pd.DataFrame()

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__
