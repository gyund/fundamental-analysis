from zipfile import ZipFile
from datetime import date
from pathlib import Path
import pandas as pd
from requests_cache import CachedSession, FileCache,SQLiteCache
from datetime import timedelta
from io import BytesIO
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

    def getCik(self, ticker: str):
        result = self._data[self._data.ticker == ticker.upper()]
        return result.cik_str.iloc[0]

    def getTicker(self, cik: int):
        result = self._data[self._data.cik_str == cik]
        return result.ticker.iloc[0]

class DataSetReader:
    def __init__(self, zip_data : bytes) -> None:
        self.zip_data = BytesIO(zip_data)

    def getData(self) -> pd.DataFrame:
        forms = ['10-K', '10-Q']
        with ZipFile(self.zip_data) as myzip:
            # Process the mapping first
            with myzip.open('sub.txt') as myfile:
                """ Contains the document type mapping to form id.
                
                adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma	
                stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi	
                fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
                """
                # Get reports that are 10-K or 10-Q
                report_list = pd.read_csv(myfile, delimiter='\t', usecols=['adsh', 'cik', 'form'])
                report_list = report_list[report_list.form.isin(forms)]

                with myzip.open('num.txt') as myfile:
                    """ Contains the data
                    adsh	tag	version	coreg	ddate	qtrs	uom	value	footnote
                    """
                    # TODO: Process with pandas and filter the columns & rows
                    # print(myfile.read())
                    data_set = pd.read_csv(myfile, delimiter='\t')
                    # Filter out the results containing only those reports
                    data_set = data_set[data_set.adsh.isin(report_list.adsh)]
                    # TODO: Store or merge with existing data
                    return data_set

class DownloadManager:

    # Format of zip example: 2023q1.zip
    _base_url = 'https://www.sec.gov/files/dera/data/financial-statement-data-sets'

    _company_tickers_url = 'https://www.sec.gov/files/company_tickers.json'

    def __init__(self, 
                 ticker_session : CachedSession,
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
        
    
class DataSetCollector:

    def __init__(self, download_manager: DownloadManager):
        self.download_manager = download_manager

    """ Take care of downloading all the data sets and aggregate them into a single structure """
    def getData(self, report_dates: list[ReportDate]) -> pd.DataFrame:
        df = pd.DataFrame
        for r in report_dates:
            reader = self.download_manager.getData(r)
            data = reader.getData()
            df.merge(data)

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
            stale_if_error=True)
        ticker_session = CachedSession(
            'tickers', 
            backend=SQLiteCache(db_path=storage_path/'tickers'), 
            expire_after=timedelta(days=365),
            stale_if_error=True)
        self.download_manager = DownloadManager(ticker_session, data_session)

    def update(self, tickers: list, years: int = 5, last_report: ReportDate = ReportDate()) -> pd.DataFrame:
        """ Update the database with information about the following stocks.

        When this command runs, it will pull updates starting from 

        Args:
            tickers (list): only store and catalog information about these tickers
            years (int): number of years to go back in time. Defaults to 5.
            last_report (ReportDate): only retrieve reports from this quarter and before

        Returns:
            pd.DataFrame: with the extracted data from the report
        """
        ticker_map = self.download_manager.getTickers()

        # Download reports for each quarter and update records for tickers specified
        download_list = Sec._getDownloadList(years, last_report)
        collector = DataSetCollector(self.download_manager)
        return collector.getData(download_list)

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
        dl_list : list[ReportDate] = list()
        next_report = last_report
        final_report = ReportDate(last_report.year-years, last_report.quarter)
        while 1:
            dl_list.append(ReportDate(year=next_report.year, quarter=next_report.quarter))
            if next_report == final_report:
                break
            if 1 == next_report.quarter:
                next_report.quarter = 4
                next_report.year -= 1
            else:
                next_report.quarter -= 1
        return dl_list
