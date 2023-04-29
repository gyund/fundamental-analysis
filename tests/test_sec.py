import pytest
import mock
import os
import io
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


@pytest.fixture
def sec_instance() -> Sec:
    # test using the real SEC adapter
    return Sec(Path(os.path.dirname(os.path.realpath(__file__))) / ".ticker-cache")


@pytest.fixture(scope='module')
def sec_fake_report() -> DataSelector:
    sub_df = DataSetReader._processSubText(
        ['10-K', '10-Q'], io.StringIO(sub_txt_sample))
    num_df = DataSetReader._processNumText(
        io.StringIO(data_txt_sample), sub_df)
    return DataSelector(num_df)


def test_DataSetReader_processSubText():
    sub_df = DataSetReader._processSubText(
        ['10-K', '10-Q'], io.StringIO(sub_txt_sample))
    logger.debug(f'sub keys: {sub_df.keys()}')
    logger.debug(sub_df)
    assert '0000320193-23-000006' in sub_df.index.get_level_values('adsh')
    assert '0000723125-23-000022' in sub_df.index.get_level_values('adsh')
    assert '0000004457-23-000026' not in sub_df.index.get_level_values('adsh')


def test_DataSetReader_processNumText(sec_fake_report: DataSelector):
    logger.debug(f'num keys: {sec_fake_report._data.keys()}')
    logger.debug(sec_fake_report._data)
    assert '0000320193-23-000006' in sec_fake_report._data.index.get_level_values(
        'adsh')
    assert '0000723125-23-000022' in sec_fake_report._data.index.get_level_values(
        'adsh')


def test_Reports_getTags(sec_fake_report: DataSelector):
    tags = sec_fake_report.getTags()
    assert len(tags) == 1
    assert 'EntityCommonStockSharesOutstanding' in tags


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


@pytest.mark.skipif(os.getenv("TICKER_TEST_SEC") is None,
                    reason="env variable TICKER_TEST_SEC not set")
def test_DownloadManager_getTickers(sec_instance: Sec):
    tickers = sec_instance.download_manager.getTickers()
    assert tickers.getCik('AAPL') == 320193
    assert tickers.getCik('aapl') == 320193
    assert tickers.getTicker(320193) == 'AAPL'


@pytest.mark.skipif(os.getenv("TICKER_TEST_SEC") is None,
                    reason="env variable TICKER_TEST_SEC not set")
def test_DownloadManager_getData(sec_instance: Sec):
    data = sec_instance.download_manager.getData(
        ReportDate(year=2023, quarter=1))
    df = data.processZip()
    assert df.empty == False
    report = DataSelector(df)

    tags = report.getTags()
    logger.debug(f'tags({len(tags)}): {tags}')
    assert len(tags) > 0
    # TODO: Verify access semantics so we can create a query API on the extracted data
    # aapl =  df[df.adsh == '0000320193-23-000005']
    # assert aapl.empty == False


@pytest.mark.skipif(os.getenv("TICKER_TEST_SEC") is None,
                    reason="env variable TICKER_TEST_SEC not set")
def test_update(sec_instance: Sec):
    pytest.skip("skip until getData is verified")
    df = sec_instance.update(
        tickers=['aapl'], years=1, last_report=ReportDate(year=2023, quarter=1))
    assert df.empty == False
    assert 'adsh' in df.keys()
    assert 'cik' in df.keys()
