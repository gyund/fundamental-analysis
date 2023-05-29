import io

import mock
import pytest
from pandas import DataFrame

import stocktracer.filter as Filter
from stocktracer.collector.sec import DataSetReader, ReportDate, TickerReader


@pytest.fixture
def filter_aapl():
    return filter_aapl_years()


def filter_aapl_years(history_in_years: int = 0) -> Filter.Selectors:
    return Filter.Selectors(
        ticker_filter=["aapl"],
        sec_filter=Filter.SecFilter(
            tags=["EntityCommonStockSharesOutstanding"],
            years=history_in_years,  # Just want the current
            last_report=ReportDate(year=2023, quarter=1),
            only_annual=False,
        ),  # We want the 10-Q
    )


@pytest.fixture
def sub_txt_sample() -> str:
    return """adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma	stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi	fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
0000723125-23-000022	723125	MICRON TECHNOLOGY INC	3674	US	ID	BOISE	83716-9632	8000 S FEDERAL WAY	PO BOX 6	2083684000	US	ID	BOISE	83716-9632	8000 S FEDERAL WAY	PO BOX 6	US	DE	751618004			1-LAF	0	0831	10-Q	20230228	2023	Q2	20230329	2023-03-29 16:48:00.0	0	1	mu-20230302_htm.xml	1
0000004457-23-000026	4457	U-HAUL HOLDING CO /NV/	7510	US	NV	RENO	89511	5555 KIETZKE LANE STE 100		7756886300	US	NV	RENO	89511	5555 KIETZKE LANE	SUITE 100	US	NV	880106815	AMERCO /NV/	19920703	1-LAF	0	0331	8-K	20230331			20230329	2023-03-29 16:05:00.0	0	0	uhal-20230323_htm.xml	1
0000320193-23-000006	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2023	Q1	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
"""


@pytest.fixture
def data_txt_sample() -> str:
    return """adsh	tag	version	coreg	ddate	qtrs	uom	value	footnote
0000320193-23-000006	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	15821946000.0000
0000723125-23-000022	EntityCommonStockSharesOutstanding	dei/2022		20230331	0	shares	1094394354.0000
"""


# This data we manufacture so that we get the match between sub_txt and data_txt,
# but the quarterly date, numbers, etc is different so we can verify the rows
# and column processing
@pytest.fixture
def fake_sub_txt_sample() -> str:
    return """adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma	stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi	fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
0000320193-23-000006	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2023	Q1	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
0000320193-23-000005	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2022	Q4	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
0000320193-23-000004	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2022	Q3	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
0000320193-23-000003	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2022	Q2	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
0000320193-23-000002	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2022	Q1	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
0000320193-23-000001	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2021	Q4	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
0000320193-23-000000	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2021	Q3	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
"""


@pytest.fixture
def fake_data_txt_sample() -> str:
    return """adsh	tag	version	coreg	ddate	qtrs	uom	value	footnote
0000320193-23-000006	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	6000.0000
0000320193-23-000005	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	5000.0000
0000320193-23-000004	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	4000.0000
0000320193-23-000003	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	3000.0000
0000320193-23-000002	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	2000.0000
0000320193-23-000001	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	1000.0000
0000320193-23-000006	FakeAttributeTag	dei/2022		20230131	0	shares	600.0000
0000320193-23-000005	FakeAttributeTag	dei/2022		20230131	0	shares	500.0000
0000320193-23-000004	FakeAttributeTag	dei/2022		20230131	0	shares	400.0000
0000320193-23-000003	FakeAttributeTag	dei/2022		20230131	0	shares	300.0000
0000320193-23-000002	FakeAttributeTag	dei/2022		20230131	0	shares	200.0000
0000320193-23-000001	FakeAttributeTag	dei/2022		20230131	0	shares	100.0000

"""


@pytest.fixture
def sec_fake_report(
    filter_aapl: Filter.Selectors, sub_txt_sample, data_txt_sample
) -> Filter.Selectors:
    filter_aapl.sec_filter._cik_list = set()
    filter_aapl.sec_filter._cik_list.add(320193)
    sub_df = DataSetReader._process_sub_text(
        filepath_or_buffer=io.StringIO(sub_txt_sample),
        sec_filter=filter_aapl.sec_filter,
    )
    num_df = DataSetReader._process_num_text(
        filepath_or_buffer=io.StringIO(data_txt_sample),
        sec_filter=filter_aapl.sec_filter,
        sub_dataframe=sub_df,
    )
    ticker_reader = mock.MagicMock(TickerReader)
    assert not num_df.empty
    return filter_aapl


@pytest.fixture
def sec_manufactured_fake_report(
    filter_aapl: Filter.Selectors, fake_sub_txt_sample, fake_data_txt_sample
) -> Filter.Selectors:
    return sec_manufactured_fake_report_impl(
        filter_aapl, fake_sub_txt_sample, fake_data_txt_sample
    )


def sec_manufactured_fake_report_impl(
    selector: Filter.Selectors, sub_txt: str, data_txt: str
) -> DataFrame:
    selector.sec_filter.tags.append("FakeAttributeTag")
    sub_df = DataSetReader._process_sub_text(
        filepath_or_buffer=io.StringIO(sub_txt),
        sec_filter=selector.sec_filter,
        ciks=frozenset({320193}),
    )
    assert sub_df is not None
    num_df = DataSetReader._process_num_text(
        filepath_or_buffer=io.StringIO(data_txt),
        sec_filter=selector.sec_filter,
        sub_dataframe=sub_df,
    )
    assert num_df is not None
    return num_df
