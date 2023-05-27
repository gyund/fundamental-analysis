"""Use tensorflow to perform automated analysis on stock tickers."""
import logging
from typing import Optional

import pandas as pd

# Load TF-DF
import tensorflow_decision_forests as tfdf
from beartype import beartype

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
            # tags=["EarningsPerShareDiluted"],
            years=5,  # Over the past 5 years
            last_report=self.options.last_report,
            only_annual=True,  # We only want the 10-K
        )

        tickers = set()
        tickers.add("aapl")
        tickers.add("msft")
        tickers.add("goog")
        tickers.add("hd")
        tickers.add("acn")
        tickers.add("nvda")
        self.options.tickers = frozenset(tickers.union(self.options.tickers))

        # Create an SEC Data Source
        table = create_normalized_sec_table(sec_filter, self.options, False)

        table.calculate_return_on_assets("ROA")
        table.calculate_net_income("net-income")
        table.calculate_delta(column_name="delta-ROA", delta_of="ROA")
        table.calculate_debt_to_assets("debt-to-assets")
        table.calculate_current_ratio("current-ratio")

        # Select Training Stocks
        train_df = table.slice(ticker=list(tickers))

        # Select Assessment Stocks
        test_df = table.slice(ticker=list(tickers.difference(self.options.tickers)))

        train_ds = tfdf.keras.pd_dataframe_to_tf_dataset(train_df, label="my_label")
        test_ds = tfdf.keras.pd_dataframe_to_tf_dataset(test_df, label="my_label")

        # Train a Random Forest model.
        model = tfdf.keras.RandomForestModel()
        model.fit(train_ds)

        # Summary of the model structure.
        model.summary()

        # Evaluate the model.
        model.evaluate(test_ds)

        # Export the model to a SavedModel.
        model.save(str(self.options.cache_path / "tf-model"))

        return pd.DataFrame()

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__
