import pytest
import stocktracer.filter as Filter
from stocktracer.data.sec import ReportDate

@pytest.fixture
def filter_aapl() -> Filter.Selectors:
    return Filter.Selectors(
        ticker_filter={"aapl"},
        sec_filter=Filter.SecFilter(
            tags=["EntityCommonStockSharesOutstanding"],
            years=0,  # Just want the current
            last_report=ReportDate(year=2023, quarter=1),
            only_annual=False,
        ),  # We want the 10-Q
    )