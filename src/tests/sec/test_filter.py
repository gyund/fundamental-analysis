import logging
from datetime import date

import numpy as np
import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.collector.sec import Filter as SecFilter
from stocktracer.collector.sec import ReportDate

logger = logging.getLogger(__name__)


class TestFilter:
    def test_getRequiredReports_default(self):
        filter = Filter.SecFilter(
            years=1,
            tags=["dummy"],
            last_report=ReportDate(year=2022, quarter=4),
        )

        required_reports = filter.required_reports

        # You might thing 1, but since companies file annual reports in different quarters,
        # we have to look at all the quarters.
        assert len(required_reports) == 5
        assert required_reports[0] == ReportDate(year=2022, quarter=4)
        assert required_reports[1] == ReportDate(year=2022, quarter=3)
        assert required_reports[2] == ReportDate(year=2022, quarter=2)
        assert required_reports[3] == ReportDate(year=2022, quarter=1)
        assert required_reports[4] == ReportDate(year=2021, quarter=4)

    def test_getRequiredReports_quarterly(self):
        filter = Filter.SecFilter(
            tags=["dummy"],
            years=1,
            last_report=ReportDate(year=2022, quarter=4),
            only_annual=False,
        )
        required_reports = filter.required_reports

        assert len(required_reports) == 5
        assert required_reports[0] == ReportDate(year=2022, quarter=4)
        assert required_reports[1] == ReportDate(year=2022, quarter=3)
        assert required_reports[2] == ReportDate(year=2022, quarter=2)
        assert required_reports[3] == ReportDate(year=2022, quarter=1)
        assert required_reports[4] == ReportDate(year=2021, quarter=4)


def test_reportDate():
    rd = ReportDate(2023, 1)
    assert rd.year == date.today().year
    assert rd.quarter == 1

    try:
        rd = ReportDate(date.today().year + 1, 1)
        pytest.fail("should throw and exception")
    except ValueError as ex:
        pass

    try:
        rd = ReportDate(date.today().year, 0)
        pytest.fail("should throw and exception")
    except ValueError as ex:
        pass

    rd = ReportDate(date.today().year, 4)
    try:
        rd = ReportDate(date.today().year, 5)
        pytest.fail("should throw and exception")
    except ValueError as ex:
        pass


class TestResults:
    def test_slice(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "MSFT"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
                "Stuff": [3, 4],
            },
        )
        data = data.set_index(["ticker", "fy"])
        result = SecFilter.Results(data)
        logger.debug(result)

        # Slice on Ticker, make sure we get the right results
        expected_data = pd.DataFrame(
            data={
                "ticker": ["MSFT"],
                "fy": [2022],
                "OperatingIncomeLoss": [20],
                "Stuff": [4],
            },
        )
        expected_data = expected_data.set_index(["ticker", "fy"])
        assert result.slice(ticker="MSFT").equals(expected_data)

        expected_data = pd.DataFrame(
            data={
                "ticker": ["MSFT"],
                "fy": [2022],
                "OperatingIncomeLoss": [20],
                "Stuff": [4],
            },
        )
        expected_data = expected_data.set_index(["ticker", "fy"])
        sliced = result.slice(year=2022)
        logger.debug(sliced)
        assert sliced.equals(expected_data)

        expected_data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "MSFT"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
            },
        )
        expected_data = expected_data.set_index(["ticker", "fy"])
        sliced = result.slice(tags=["OperatingIncomeLoss"])
        logger.debug(sliced)
        assert sliced.equals(expected_data)

    def test_net_income(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "AAPL"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
            },
        )
        data = data.set_index(["ticker", "fy"])
        result = SecFilter.Results(data)
        result.calculate_net_income("net-income")
        logger.debug(f"\n{data}")
        assert result.data["net-income"].sum() == 30
        assert result.data.loc["AAPL"].loc[2022]["net-income"] == 20

    def test_return_on_assets(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "AAPL"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
                "Assets": [20, 80],
            },
        )
        data = data.set_index(["ticker", "fy"])
        result = SecFilter.Results(data)
        result.calculate_return_on_assets("ROA")
        logger.debug(f"\n{data}")
        assert result.data.loc["AAPL"].loc[2021]["ROA"] == 0.50
        assert result.data.loc["AAPL"].loc[2022]["ROA"] == 0.25

    def test_calculate_delta(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "AAPL"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
                "Assets": [20, 80],
            },
        )
        data = data.set_index(["ticker", "fy"])
        result = SecFilter.Results(data)
        result.calculate_delta("delta", "OperatingIncomeLoss")
        logger.debug(f"\n{data}")
        assert np.isnan(result.data.loc["AAPL"].loc[2021]["delta"])
        assert result.data.loc["AAPL"].loc[2022]["delta"] == 10

    def test_current_ratio(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "AAPL"],
                "fy": [2021, 2022],
                "AssetsCurrent": [10, 20],
                "LiabilitiesCurrent": [20, 80],
            },
        )
        data = data.set_index(["ticker", "fy"])
        result = SecFilter.Results(data)
        result.calculate_current_ratio("CR")
        assert result.data.loc["AAPL"].loc[2021]["CR"] == 0.5
        assert result.data.loc["AAPL"].loc[2022]["CR"] == 0.25

    def test_debt_to_assets(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "AAPL"],
                "fy": [2021, 2022],
                "AssetsCurrent": [10, 20],
                "LiabilitiesCurrent": [20, 80],
            },
        )
        data = data.set_index(["ticker", "fy"])
        result = SecFilter.Results(data)
        result.calculate_debt_to_assets("CR")
        assert result.data.loc["AAPL"].loc[2021]["CR"] == 2
        assert result.data.loc["AAPL"].loc[2022]["CR"] == 4
