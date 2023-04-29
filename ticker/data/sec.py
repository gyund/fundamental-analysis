from zipfile import ZipFile
from datetime import date
from pathlib import Path
import pandas as pd
from requests_cache import CachedSession, FileCache, SQLiteCache
from datetime import timedelta
from io import BytesIO
from typing import Literal, get_args
import logging
logger = logging.getLogger(__name__)


class ReportDate:

    def __init__(self,
                 year: int = date.today().year,
                 quarter: int = ((date.today().month-1) / 3) + 1):
        if year > date.today().year:
            raise ValueError(
                "you cannot request reports in the future...that would be illegal :)")
        if not quarter in range(1, 5):
            raise ValueError(
                "the value for the quarter must be a value between 1 and 4")
        self.year = year
        self.quarter = quarter

    def __eq__(self, other: 'ReportDate') -> bool:
        """

        Args:
            other ('ReportDate'): _description_

        Returns:
            bool: true if equal
        """
        return self.quarter == other.quarter and self.year == other.year


class TickerReader:

    def __init__(self, data: bytes):
        self._data = pd.read_json(data, orient='index')

    def getCik(self, ticker: str) -> int:
        """ Get the Cik from the stock ticker

        Args:
            ticker (str): stock ticker. The case does not matter.

        Returns:
            int: cik
        """
        result = self._data[self._data.ticker == ticker.upper()]
        return result.cik_str.iloc[0]

    def getTicker(self, cik: int) -> str:
        """ Get the stock ticker from the Cik number

        Args:
            cik (int): Cik number for the stock

        Returns:
            str: stock ticker
        """
        result = self._data[self._data.cik_str == cik]
        return result.ticker.iloc[0]


class DataSetReader:
    """ Reads the data from a zip file retrieved from the SEC website 
    """

    def __init__(self, zip_data: bytes) -> None:
        self.zip_data = BytesIO(zip_data)

    def processZip(self) -> pd.DataFrame:
        forms = ['10-K', '10-Q']
        with ZipFile(self.zip_data) as myzip:
            # Process the mapping first
            logger.debug('opening sub.txt')
            with myzip.open('sub.txt') as myfile:

                # Get reports that are 10-K or 10-Q
                sub_dataframe = DataSetReader._processSubText(forms, myfile)

                with myzip.open('num.txt') as myfile:
                    return DataSetReader._processNumText(myfile, sub_dataframe)

    def _processNumText(filepath_or_buffer, sub_dataframe) -> pd.DataFrame:
        """ Contains the document type mapping to form id.

            adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma	
            stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi	
            fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
        """
        logger.debug('processing num.txt')
        data_set = pd.read_csv(
            filepath_or_buffer, delimiter='\t', index_col=['adsh', 'tag'])
        # Filter out the results containing only those reports
        logger.debug('filtering out reports')
        logger.debug(data_set.head())
        # We want only the tables in left if they join on the key, so inner it is
        return data_set.join(sub_dataframe, how='inner')

    def _processSubText(forms, filepath_or_buffer) -> pd.DataFrame:
        """ Contains the data
            adsh	tag	version	coreg	ddate	qtrs	uom	value	footnote
        """
        logger.debug('processing sub.txt')
        report_list = pd.read_csv(filepath_or_buffer, delimiter='\t', usecols=['adsh', 'cik', 'form'],
                                  index_col=['adsh', 'cik'])
        logger.debug(f'keeping only these forms: {forms}')
        report_list = report_list[report_list.form.isin(forms)]
        logger.debug(report_list.head())
        return report_list


class DownloadManager:

    # Format of zip example: 2023q1.zip
    _base_url = 'https://www.sec.gov/files/dera/data/financial-statement-data-sets'

    _company_tickers_url = 'https://www.sec.gov/files/company_tickers.json'

    def __init__(self,
                 ticker_session: CachedSession,
                 data_session: CachedSession) -> None:
        self._ticker_session = ticker_session
        self._data_session = data_session

    def getTickers(self) -> TickerReader:
        """Get the CIK ticker mappings. This must be done before processing reports

        The SEC stores the mappings of the CIK values to tickers in a JSON file.
        We can download and cache this information essentially for a year. We're 
        not interested in companies that recently listed because they don't have a 
        long regulated record of reported earnings. When we process the records, we can 
        ignore cik values that are not in this list.


        Typical json for these looks like the following (without spaces or line breaks):

        {"0":{"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."},
         "1":{"cik_str":789019,"ticker":"MSFT","title":"MICROSOFT CORP"},

        Returns:
            TickerReader: maps cik to stock ticker

        """
        response = self._ticker_session.get(self._company_tickers_url)
        if response.from_cache:
            logger.info("Retrieved tickers->cik mapping from cache")
        if response.status_code == 200:
            return TickerReader(response.content.decode())
        else:
            return TickerReader(pd.DataFrame())

    def _createDownloadUri(self, report_date: ReportDate) -> str:
        file = f"{report_date.year}q{report_date.quarter}.zip"
        return '/'.join([self._base_url, file])

    def getData(self, report_date: ReportDate) -> DataSetReader:
        request = self._createDownloadUri(report_date)
        response = self._data_session.get(request)
        if response.from_cache:
            logger.info(f"Retrieved {request} from cache")
        if response.status_code == 200:
            return DataSetReader(response.content)
        else:
            return DataSetReader(pd.DataFrame())


class DataSelector:
    """ A DataSelector contains all the data we know about. 

    The purpose of this class is to narrow down and select relevant subsets of the data
    based on specific criteria. 
    """
    _report_types = Literal['quarterly', 'annual']
    _period_focus = Literal['FY', 'Q1', 'Q2', 'Q3', 'Q4']

    def __init__(self, data: pd.DataFrame, ticker_reader: TickerReader) -> None:
        self.data = data
        self._ticker_reader = ticker_reader

    def getTags(self) -> pd.Index:
        return self.data.index.get_level_values('tag').unique()

    def _getCik(self, ticker: str):
        return self._ticker_reader.getCik(ticker)

    def _getFormType(self, report_type: _report_types):
        assert report_type in get_args(self._report_types)
        if 'quarterly' == report_type:
            return '10-Q'
        elif 'annual' == report_type:
            return '10-K'

    def filterStockByTicker(self, data: pd.DataFrame, ticker: str):
        cik = self._getCik(ticker)
        return data.query(f'cik == {cik}')

    def filterStockByForm(self, data: pd.DataFrame, form: str):
        return data.query(f"form == '{form.upper()}'")

    def select(
            self,
            report_type: _report_types,
            ticker: str,
            period_focus: _period_focus = None
    ) -> pd.DataFrame:
        """_summary_

        Args:
            report_type (_report_types): type of report can be 'yearly' or 'quarterly'
            ticker (str): ticker symbol for the company
            period_focus (_period_focus): Focus of the report can be 'FY' = Yearly, Q1,Q2,Q3,Q4

        Returns:
            pd.DataFrame: filtered DataFrame
        """
        form = self._getFormType(report_type)
        assert True == isinstance(ticker, str)
        # Filter out the Stock
        df = self.filterStockByTicker(self.data, ticker=ticker)
        # Filter out quarterly/annual
        df = self.filterStockByForm(self.data, form=form)
        # # Filter out the data range
        # if period_focus is not None:
        #     return
        return df


class DataSetCollector:

    def __init__(self, download_manager: DownloadManager):
        self.download_manager = download_manager

    """ Take care of downloading all the data sets and aggregate them into a single structure """

    def getData(self, report_dates: list[ReportDate]) -> pd.DataFrame:
        df = None
        logger.info(
            f"Creating Unified Data record for these reports: {report_dates}")
        for r in report_dates:
            reader = self.download_manager.getData(r)
            data = reader.processZip()
            if df is None:
                logger.debug(f"keys: {data.keys()}")
                df = data
            else:
                # df = pd.concat(df, data)
                df.merge(right=data)
        logger.info(
            f"Created Unified Data record for these reports: {report_dates}")
        logger.debug(f"keys: {df.keys()}")
        logger.debug(f"Rows: {len(df)}")
        logger.debug(df.head())
        return df


class Sec:

    data: pd.DataFrame = None

    def __init__(self, storage_path: Path):
        if not isinstance(storage_path, Path):
            raise ValueError("storage_path is required")
        storage_path.mkdir(parents=True, exist_ok=True)
        data_session = CachedSession(
            'data',
            backend=SQLiteCache(db_path=storage_path/'data'),
            serializer='pickle',
            expire_after=timedelta(days=365*5),
            stale_if_error=True)
        ticker_session = CachedSession(
            'tickers',
            backend=SQLiteCache(db_path=storage_path/'tickers'),
            expire_after=timedelta(days=365),
            stale_if_error=True)
        self.download_manager = DownloadManager(ticker_session, data_session)

    def update(self, tickers: list, years: int = 5, last_report: ReportDate = ReportDate()) -> DataSelector:
        """ Update the database with information about the following stocks.

        When this command runs, it will pull updates starting from 

        Args:
            tickers (list): only store and catalog information about these tickers
            years (int): number of years to go back in time. Defaults to 5.
            last_report (ReportDate): only retrieve reports from this quarter and before

        Returns:
            DataSelector: with the extracted data from the report
        """
        # Download reports for each quarter and update records for tickers specified
        download_list = Sec._getDownloadList(years, last_report)
        collector = DataSetCollector(self.download_manager)
        data = collector.getData(download_list)
        ticker_map = self.download_manager.getTickers()
        return DataSelector(data, ticker_map)

    def _getDownloadList(years: int, last_report: ReportDate) -> list[ReportDate]:
        """ Get a list of files to download for all the quarters.

        The list generated will include an extra quarter so that you will always be
        able to do analysis from the current quarter to the previous quarter.

        Args:
            years (int): number of years to go back in time.
            last_report (ReportDate): only retrieve reports from this quarter and before

        Returns:
            list[ReportDate]: list of report dates to retrieve
        """
        dl_list: list[ReportDate] = list()
        next_report = last_report
        final_report = ReportDate(last_report.year-years, last_report.quarter)
        while 1:
            dl_list.append(ReportDate(year=next_report.year,
                           quarter=next_report.quarter))
            if next_report == final_report:
                break
            if 1 == next_report.quarter:
                next_report.quarter = 4
                next_report.year -= 1
            else:
                next_report.quarter -= 1
        return dl_list
