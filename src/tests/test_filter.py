import pytest

import stocktracer.filter as Filter
from stocktracer.data.sec import Filter as SecFilter


def test_Selectors_init():
    with pytest.raises(TypeError, match="missing 2 required positional arguments"):
        Filter.Selectors()
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        Filter.Selectors(ticker_filter={"aapl"})

    default_selector = Filter.Selectors(ticker_filter={"aapl"}, sec_filter=SecFilter())
    assert default_selector.sec_filter.last_report is not None
    assert default_selector.sec_filter.only_annual is True
    selector = Filter.Selectors(
        ticker_filter={"aapl"},
        sec_filter=SecFilter(tags=["EntityCommonStockSharesOutstanding"]),
    )
    assert "aapl" in selector.ticker_filter
    assert "EntityCommonStockSharesOutstanding" in selector.sec_filter.tags

    selector = Filter.Selectors(
        ticker_filter=["aapl"],
        sec_filter=SecFilter(tags=["EntityCommonStockSharesOutstanding"]),
    )
    assert "aapl" in selector.ticker_filter
    assert "EntityCommonStockSharesOutstanding" in selector.sec_filter.tags
