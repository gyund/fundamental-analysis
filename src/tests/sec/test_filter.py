import logging
from datetime import date

import numpy as np
import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.collector.sec import Filter as SecFilter
from stocktracer.collector.sec import ReportDate
from stocktracer.collector.sec import Results as SecResults
from io import StringIO

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
    @classmethod
    def _prepare_table(cls, df: pd.DataFrame) -> SecResults.Table:
        data = df.set_index(["ticker", "fy"])
        return SecResults.Table(data)

    def test_tags(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "MSFT"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
                "Stuff": [3, 4],
            },
        )
        result = self._prepare_table(data)
        assert "OperatingIncomeLoss" in result.tags

    def test_get_value(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "MSFT"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
                "Stuff": [3, 4],
            },
        )
        result = self._prepare_table(data)
        logger.debug(result)
        assert (
            result.get_value(ticker="AAPL", tag="OperatingIncomeLoss", year=2021) == 10
        )

    def test_normalize(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "MSFT"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
                "Stuff": [np.nan, 4],
            },
        )
        result = self._prepare_table(data)
        assert "Stuff" in result.tags
        result.normalize()
        assert "Stuff" not in result.tags

    def test_select(self):
        csv_data = """ticker,tag,fy,fp,ddate,uom,value,period,title
AAPL,EntityCommonStockSharesOutstanding,2022,Q1,2023-01-31,shares,2000.0,2022-12-31,Apple Inc.
AAPL,FakeAttributeTag,2022,Q1,2023-01-31,shares,200.0,2022-12-31,Apple Inc."""
        df = pd.read_csv(StringIO(csv_data))
        assert not df.empty
        results = SecResults(df)
        logger.debug(f"\n{results}")
        select_results = results.select()
        logger.debug(f"\n{select_results}")
        assert (
            select_results.get_value("aapl", "EntityCommonStockSharesOutstanding", 2022)
            == 2000
        )

    def test_slice(self):
        data = pd.DataFrame(
            data={
                "ticker": ["AAPL", "MSFT"],
                "fy": [2021, 2022],
                "OperatingIncomeLoss": [10, 20],
                "Stuff": [3, 4],
            },
        )
        result = self._prepare_table(data)
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
        result = self._prepare_table(data)
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
        result = self._prepare_table(data)
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
        result = self._prepare_table(data)
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
        result = self._prepare_table(data)
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
        result = self._prepare_table(data)
        result.calculate_debt_to_assets("CR")
        assert result.data.loc["AAPL"].loc[2021]["CR"] == 2
        assert result.data.loc["AAPL"].loc[2022]["CR"] == 4
