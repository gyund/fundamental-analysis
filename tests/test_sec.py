import pytest
import mock
import os
import io
from tests.fixtures.network.sec import sec_instance, sec_dataselector_2023q1
from ticker.cli import Cli
from ticker.data.sec import Sec, ReportDate, TickerReader, DataSetReader, DataSelector
from datetime import date
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

sub_txt_sample = """adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma	stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi	fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
0000723125-23-000022	723125	MICRON TECHNOLOGY INC	3674	US	ID	BOISE	83716-9632	8000 S FEDERAL WAY	PO BOX 6	2083684000	US	ID	BOISE	83716-9632	8000 S FEDERAL WAY	PO BOX 6	US	DE	751618004			1-LAF	0	0831	10-Q	20230228	2023	Q2	20230329	2023-03-29 16:48:00.0	0	1	mu-20230302_htm.xml	1
0000004457-23-000026	4457	U-HAUL HOLDING CO /NV/	7510	US	NV	RENO	89511	5555 KIETZKE LANE STE 100		7756886300	US	NV	RENO	89511	5555 KIETZKE LANE	SUITE 100	US	NV	880106815	AMERCO /NV/	19920703	1-LAF	0	0331	8-K	20230331			20230329	2023-03-29 16:05:00.0	0	0	uhal-20230323_htm.xml	1
0000320193-23-000006	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2023	Q1	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
"""

data_txt_sample = """adsh	tag	version	coreg	ddate	qtrs	uom	value	footnote
0000320193-23-000006	EntityCommonStockSharesOutstanding	dei/2022		20230131	0	shares	15821946000.0000
0000723125-23-000022	EntityCommonStockSharesOutstanding	dei/2022		20230331	0	shares	1094394354.0000
"""


@pytest.fixture(scope='module')
def sec_fake_report() -> DataSelector:
    sub_df = DataSetReader._processSubText(
        ['10-K', '10-Q'], io.StringIO(sub_txt_sample))
    num_df = DataSetReader._processNumText(
        io.StringIO(data_txt_sample), sub_df)
    ticker_reader = mock.MagicMock()
    return DataSelector(num_df, ticker_reader)


def test_DataSetReader_processSubText():
    sub_df = DataSetReader._processSubText(
        ['10-K', '10-Q'], io.StringIO(sub_txt_sample))
    logger.debug(f'sub keys: {sub_df.keys()}')
    logger.debug(sub_df)
    assert '0000320193-23-000006' in sub_df.index.get_level_values('adsh')
    assert '0000723125-23-000022' in sub_df.index.get_level_values('adsh')
    assert '0000004457-23-000026' not in sub_df.index.get_level_values('adsh')


class TestDataSelector:

    def test_processNumText(self, sec_fake_report: DataSelector):
        logger.debug(f'num keys: {sec_fake_report.data.keys()}')
        logger.debug(sec_fake_report.data)
        assert '0000320193-23-000006' in sec_fake_report.data.index.get_level_values(
            'adsh')
        assert '0000723125-23-000022' in sec_fake_report.data.index.get_level_values(
            'adsh')
        logger.debug(f"keys in data: {sec_fake_report.data.keys()}")
        assert 'value' in sec_fake_report.data.keys()
        logger.debug(
            f"index for cik: {sec_fake_report.data.index.names}")
        assert 'adsh' in sec_fake_report.data.index.names
        assert 'tag' in sec_fake_report.data.index.names
        assert 'cik' in sec_fake_report.data.index.names

    def test_getTags(self, sec_fake_report: DataSelector):
        tags = sec_fake_report.getTags()
        assert len(tags) == 1
        assert 'EntityCommonStockSharesOutstanding' in tags

    def test_filterStockByTicker(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._getCik = mock.Mock(
            return_value=320193)
        df = sec_fake_report.filterStockByTicker(
            sec_fake_report.data, ticker='AAPL')
        assert df is not None
        assert 1 == len(df)

    def test_filterStockByForm(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        df = sec_fake_report.filterStockByForm(
            sec_fake_report.data, form='10-Q')
        assert df is not None
        assert 2 == len(df)

    def test_select_quarterly(self, sec_fake_report: DataSelector):
        # Create a sample set of typical queries one might make with the DataSelector
        sec_fake_report._ticker_reader.getTicker = mock.Mock(
            return_value=320193)
        df = sec_fake_report.select(
            report_type="quarterly", ticker='AAPL', years=0)
        assert df is not None


def test_reportDate():
    rd = ReportDate(2023, 1)
    assert rd.year == date.today().year
    assert rd.quarter == 1

    try:
        rd = ReportDate(date.today().year+1, 1)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass

    try:
        rd = ReportDate(date.today().year, 0)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass

    rd = ReportDate(date.today().year, 4)
    try:
        rd = ReportDate(date.today().year, 5)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass


def test_getDownloadList_1():
    dl_list = Sec._getDownloadList(
        years=1, last_report=ReportDate(year=2022, quarter=4))
    assert len(dl_list) == 5
    assert dl_list[0] == ReportDate(year=2022, quarter=4)
    assert dl_list[1] == ReportDate(year=2022, quarter=3)
    assert dl_list[2] == ReportDate(year=2022, quarter=2)
    assert dl_list[3] == ReportDate(year=2022, quarter=1)
    assert dl_list[4] == ReportDate(year=2021, quarter=4)
