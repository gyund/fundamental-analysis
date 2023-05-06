import logging
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional, get_args
from zipfile import ZipFile

import numpy as np
import pandas as pd
from beartype import beartype
from requests_cache import CachedSession, FileCache, SQLiteCache

logger = logging.getLogger(__name__)

default_chunk_size = 1000000


@beartype
class ReportDate:
    def __init__(
        self,
        year: int = date.today().year,
        quarter: int = ((date.today().month - 1) // 3) + 1,
    ):
        if year > date.today().year:
            raise ValueError(
                "you cannot request reports in the future...that would be illegal :)"
            )
        if not quarter in range(1, 5):
            raise ValueError(
                f"the quarter must be a value between 1 and 4 - given: {quarter}"
            )
        self.year = year
        self.quarter = quarter

    def __str__(self) -> str:
        return f"{self.year}-q{self.quarter}"

    def __repr__(self) -> str:
        return f"ReportDate({self.year},{self.quarter})"

    def __eq__(self, other: "ReportDate") -> bool:
        """

        Args:
            other ('ReportDate'): _description_

        Returns:
            bool: true if equal
        """
        return self.quarter == other.quarter and self.year == other.year


@beartype
class TickerReader:
    def __init__(self, data: str):
        self._data = pd.read_json(data, orient="index")

    def getCik(self, ticker: str) -> np.int64:
        """Get the Cik from the stock ticker

        Args:
            ticker (str): stock ticker. The case does not matter.

        Raises:
            LookupError: If ticker is not found

        Returns:
            int: cik
        """
        result = self._data[self._data.ticker == ticker.upper()]
        if result.empty:
            raise LookupError(f"unable to find ticker: {ticker}")
        return result.cik_str.iloc[0]

    def getTicker(self, cik: int) -> str:
        """Get the stock ticker from the Cik number

        Args:
            cik (int): Cik number for the stock

        Returns:
            str: stock ticker
        """
        result = self._data[self._data.cik_str == cik]
        return result.ticker.iloc[0]

    def contains(self, tickers: frozenset) -> bool:
        """Check that the tickers provided exist

        Args:
            tickers (frozenset): tickers to check

        Returns:
            bool: if all the tickers are found
        """
        try:
            for t in tickers:
                self.getCik(t)
        except LookupError:
            return False
        return True


period_focus_options = Literal["FY", "Q1", "Q2", "Q3", "Q4"]


@beartype
class Filter:
    def __init__(
        self,
        tags: list[str],
        years: int = 5,
        last_report: ReportDate = ReportDate(),
        only_annual: bool = True,
    ) -> None:
        """Filter for SEC tools to scrape relevant information when processing records.

        This is an important concept to dealing with large data sets. It allows us to chunk processing
        into batches and find/locate only records of interest. Without these filters, the tool would
        require absurd amounts of memory and storage to process.

        Args:
            tags (list[str]): list of tags found in the SEC report, such as 'EntityCommonStockSharesOutstanding'
            years (int): years of reports desired. Defaults to 5.
            last_report (ReportDate): most recent SEC data dump identified by the year an quarter. Defaults to ReportDate().
            only_annual (bool): If true, only scrape the annual reports. Defaults to True.
        """
        self.tags = tags
        self.years = years
        self.last_report = last_report
        self.only_annual = only_annual
        self._cik_list: set[int] = None

    def __str__(self) -> str:
        """
        >>> print(Filter(["Income","Debt"],5,ReportDate(2023,1)))
        Filter on 2023-q1 and the previous 5 years
        Annual Only: True
        CIK(s): None
        Tags: Income,Debt
        """
        return f"""Filter on {self.last_report} and the previous {self.years} years
Annual Only: {self.only_annual}
CIK(s): {','.join([str(i) for i in self._cik_list]) if self._cik_list else 'None'}
Tags: {','.join(self.tags) if self.tags else 'None'}"""

    def getCikList(self) -> set[int]:
        """Retrieves a list of CIK values corresponding to the tickers being looked up

        The SEC object will call populateCikList to generate this information. This helps
        with dependency injection by avoiding the Filter having to maintain references to
        these helper objects for temporary processing. It also lets us stub out the information
        provided without having to involve heavier utilities or network access.

        Raises:
            LookupError: _description_

        Returns:
            set[int]: Set containing all the CIKs that are being filtered out
        """
        if self._cik_list is None:
            raise LookupError(
                "Filter was not provided a mapping of cik's based on the tickers."
            )
        return self._cik_list

    def populateCikList(
        self, tickers: frozenset[str], ticker_reader: TickerReader
    ) -> None:
        """Populates the filter's CIK list to be used for filtering.

        The Filter doesn't need the ticker symbols. If we expand to other data sources,
        we would have to repeat ticker symbols. For now, the only info we need in the
        report is the CIK values to find the corresponding stocks.

        Args:
            tickers (frozenset[str]): ticker symbols to search for
            ticker_reader (TickerReader): reader to convert ticker symbols to CIK values
        """
        self._cik_list = set()
        for ticker in tickers:
            cik = ticker_reader.getCik(ticker)
            self._cik_list.add(cik)

    def getFocusPeriod(self) -> list[str]:
        """Get the focus period for the report

        Companies file quarterly reports. The annual report replaces the quarterly
        report depending on when that is reported. Typically Q4 is replaced with FY
        for the annual reports.

        Returns:
            list[str]: list of focus periods to use for the filter
        """
        if self.only_annual:
            return ["FY"]
        else:
            return ["FY", "Q1", "Q2", "Q3", "Q4"]

    def getRequiredReports(self) -> list[ReportDate]:
        """Get a list of required reports to download for all the quarters.

        The list generated will include an extra quarter so that you will always be
        able to do analysis from the current quarter to the previous quarter.

        Also note that it doesn't matter if you specify only_annual=True. Because
        companies don't have the same fiscal year, we have to check every quarterly
        report just to see if their annual report is in there.

        Returns:
            list[ReportDate]: list of report dates to retrieve
        """
        dl_list: list[ReportDate] = list()
        next_report = self.last_report
        final_report = ReportDate(
            self.last_report.year - self.years, self.last_report.quarter
        )
        while 1:
            dl_list.append(
                ReportDate(year=next_report.year, quarter=next_report.quarter)
            )
            if next_report == final_report:
                break
            if 1 == next_report.quarter:
                next_report.quarter = 4
                next_report.year -= 1
            else:
                next_report.quarter -= 1
        return dl_list


@beartype
class DataSetReader:
    """Reads the data from a zip file retrieved from the SEC website"""

    def __init__(self, zip_data: bytes) -> None:
        self.zip_data = BytesIO(zip_data)

    def processZip(self, filter: Filter) -> pd.DataFrame:
        """Process a zip archive with the provided filter

        Args:
            filter (Filter): results to filter out of the zip archive

        Raises:
            ImportError: the filter doesn't match anything

        Returns:
            pd.DataFrame: filtered data
        """
        with ZipFile(self.zip_data) as myzip:
            # Process the mapping first
            logger.debug("opening sub.txt")
            with myzip.open("sub.txt") as myfile:
                # Get reports that are 10-K or 10-Q
                sub_dataframe = DataSetReader._processSubText(myfile, filter)

                if sub_dataframe is None or sub_dataframe.empty:
                    raise ImportError("nothing found in sub.txt matching the filter")

                with myzip.open("num.txt") as myfile:
                    return DataSetReader._processNumText(myfile, filter, sub_dataframe)

    def _processNumText(
        filepath_or_buffer, filter: Filter, sub_dataframe: pd.DataFrame
    ) -> pd.DataFrame:
        """Contains the numerical data

        adsh	tag	version	coreg	ddate	qtrs	uom	value	footnote

        """
        logger.debug("processing num.txt")
        reader = pd.read_csv(
            filepath_or_buffer,
            delimiter="\t",
            usecols=["adsh", "tag", "ddate", "uom", "value"],
            index_col=["adsh", "tag"],
            chunksize=default_chunk_size,
            parse_dates=["ddate"],
        )

        filtered_data: pd.DataFrame = None
        chunk: pd.DataFrame
        for chunk in reader:
            # We want only the tables in left if they join on the key, so inner it is
            data = chunk.join(sub_dataframe, how="inner")
            tag_list = filter.tags
            data = data.query("tag in @tag_list")
            if data.empty:  # pragma: no cover
                logger.debug(f"chunk:\n{chunk}")
                logger.debug(f"sub_dataframe:\n{sub_dataframe}")
                continue

            if filtered_data is None:
                filtered_data = data
            else:
                filtered_data.merge(data)

            filtered_data.merge(data)
        if filtered_data is not None:  # pragma: no cover
            logger.debug(f"Filtered Records (head+5): {filtered_data.head()}")
        return filtered_data

    def _processSubText(filepath_or_buffer, filter: Filter) -> Optional[pd.DataFrame]:
        """Contains the submissions

        adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma
        stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi
        fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
        """
        assert True == isinstance(filter, Filter)
        logger.debug("processing sub.txt")
        focus_periods = filter.getFocusPeriod()
        cik_list = filter.getCikList()

        oldest_fy = filter.last_report.year - filter.years
        query_str = f"cik in @cik_list and fp in @focus_periods and fy >= {oldest_fy}"
        logger.debug(f"Query string: {query_str}")
        reader = pd.read_csv(
            filepath_or_buffer,
            delimiter="\t",
            usecols=["adsh", "cik", "period", "fy", "fp"],
            index_col=["adsh", "cik"],
            chunksize=default_chunk_size,
            parse_dates=["period"],
        )
        logger.debug(f"keeping only these focus periods: {focus_periods}")
        filtered_data: pd.DataFrame = None
        chunk: pd.DataFrame
        for chunk in reader:
            data = chunk.query(query_str)
            if data.empty:
                continue
            if filtered_data is None:
                filtered_data = data
            else:
                filtered_data.merge(data)
        if filtered_data is not None:
            logger.debug(f"Filtered Records (head+5):\n{filtered_data.head()}")
        return filtered_data


@beartype
class DownloadManager:
    # Format of zip example: 2023q1.zip
    _base_url = "https://www.sec.gov/files/dera/data/financial-statement-data-sets"

    _company_tickers_url = "https://www.sec.gov/files/company_tickers.json"

    def __init__(
        self, ticker_session: CachedSession, data_session: CachedSession
    ) -> None:
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
        if response.from_cache:  # pragma: no cover
            logger.info("Retrieved tickers->cik mapping from cache")
        if response.status_code == 200:  # pragma: no cover
            return TickerReader(response.content.decode())
        else:  # pragma: no cover
            return TickerReader(pd.DataFrame())

    def _createDownloadUri(self, report_date: ReportDate) -> str:
        file = f"{report_date.year}q{report_date.quarter}.zip"
        return "/".join([self._base_url, file])

    def getData(self, report_date: ReportDate) -> DataSetReader:
        """Retrieves from a cache or makes a request to retrieve archived quarterly data.

        This allows us to download data independent of actually processing it, allowing
        us to prefetch information we need if we like.

        Args:
            report_date (ReportDate): information specifying the quarterly dump to retrieve

        Returns:
            DataSetReader: this object helps process the data received more granularly
        """
        request = self._createDownloadUri(report_date)
        response = self._data_session.get(request)
        if response.from_cache:
            logger.info(f"Retrieved {request} from cache")
        if response.status_code == 200:
            return DataSetReader(response.content)
        else:
            return DataSetReader(pd.DataFrame())


@beartype
class DataSelector:
    """A DataSelector contains all the data we know about.

    The purpose of this class is to narrow down and select relevant subsets of the data
    based on specific criteria.
    """

    _report_types = Literal["quarterly", "annual"]
    _period_focus = Literal["FY", "Q1", "Q2", "Q3", "Q4"]

    def __init__(self, data: pd.DataFrame, ticker_reader: TickerReader) -> None:
        """Class for helping select data

        This helps the user to some extent avoid some specifics about the pandas table structure.

        Args:
            data (pd.DataFrame): Filtered data from processing
            ticker_reader (TickerReader): Reader that helps convert tickers to CIKs
        """
        self.data: pd.DataFrame = data
        self._ticker_reader: TickerReader = ticker_reader

    def getTags(self) -> pd.Index:
        """Get a list of the tag values filtered from the results

        Returns:
            pd.Index: tag values
        """
        return self.data.index.get_level_values("tag").unique()

    def _getCik(self, ticker: str):
        return self._ticker_reader.getCik(ticker)

    def filterByTicker(self, ticker: str, data: pd.DataFrame = None) -> pd.DataFrame:
        """Filter results using the ticker symbol.

        Args:
            ticker (str): ticker to select
            data (pd.DataFrame): alternate data to use for filtering. Use this if you've previously filtered the data and are using this in addition.

        Returns:
            pd.DataFrame: Filtered result containing ticker results
        """
        assert isinstance(ticker, str)
        assert data is None or isinstance(data, pd.DataFrame)
        cik = self._getCik(ticker)

        # Supply the object default if not provided in the method
        if data is None or data.empty:
            data = self.data
        return data.query(f"cik == {cik}")

    def select(
        self,
        ticker: str,
    ) -> pd.DataFrame:
        """Select only a subset of the data matching the specified criteria

        Args:
            ticker (str): ticker symbol for the company

        Returns:
            pd.DataFrame: filtered DataFrame
        """
        assert True == isinstance(ticker, str)
        # Filter out the Stock
        df = self.filterByTicker(ticker=ticker)
        return df


@beartype
class DataSetCollector:
    def __init__(self, download_manager: DownloadManager):
        self.download_manager = download_manager

    """ Take care of downloading all the data sets and aggregate them into a single structure """

    def getData(self, filter: Filter) -> pd.DataFrame:
        """Collect data based on the provided filter

        Args:
            filter (Filter): SEC specific filter of how to filter the results

        Returns:
            pd.DataFrame: filtered results
        """
        assert isinstance(filter, Filter)
        df = None
        report_dates = filter.getRequiredReports()
        logger.info(f"Creating Unified Data record for these reports: {report_dates}")
        for r in report_dates:
            reader = self.download_manager.getData(r)
            try:
                data = reader.processZip(filter)
                if df is None:
                    logger.debug(f"keys: {data.keys()}")
                    df = data
                else:
                    # df = pd.concat(df, data)
                    df.merge(right=data)
            except ImportError as e:
                # Note, when searching for annual reports, this will generally occur 1/4 times
                # if we're only searching for one stock's tags
                logger.debug(f"{r} did not have any matches for the provided filter")
                logger.debug(f"{filter}")
        logger.info(f"Created Unified Data record for these reports: {report_dates}")
        logger.debug(f"keys: {df.keys()}")
        logger.debug(f"Rows: {len(df)}")
        logger.debug(df.head())
        return df


@beartype
class Sec:
    def __init__(self, storage_path: Path):
        if not isinstance(storage_path, Path):
            raise ValueError("storage_path is required")
        storage_path.mkdir(parents=True, exist_ok=True)
        data_session = CachedSession(
            "data",
            backend=SQLiteCache(db_path=storage_path / "data"),
            serializer="pickle",
            expire_after=timedelta(days=365 * 5),
            stale_if_error=True,
        )
        ticker_session = CachedSession(
            "tickers",
            backend=SQLiteCache(db_path=storage_path / "tickers"),
            expire_after=timedelta(days=365),
            stale_if_error=True,
        )
        self.download_manager = DownloadManager(ticker_session, data_session)

    def getData(self, tickers: frozenset[str], filter: Filter) -> DataSelector:
        """Initiate the retrieval of ticker information based on the provided filters.

        Args:
            tickers (frozenset[str]): ticker symbols you want information about
            filter (Filter): SEC specific data to scrape from the reports

        Returns:
            DataSelector: Helper for processing the filtered results
        """
        collector = DataSetCollector(self.download_manager)
        ticker_map = self.download_manager.getTickers()
        ticker_map.contains(tickers)
        filter.populateCikList(tickers=tickers, ticker_reader=ticker_map)
        filtered_data = collector.getData(filter)
        return DataSelector(data=filtered_data, ticker_reader=ticker_map)

    # def update(self, tickers: list, years: int = 5, last_report: ReportDate = ReportDate()) -> DataSelector:
    #     """ Update the database with information about the following stocks.

    #     When this command runs, it will pull updates starting from

    #     Args:
    #         tickers (list): only store and catalog information about these tickers
    #         years (int): number of years to go back in time. Defaults to 5.
    #         last_report (ReportDate): only retrieve reports from this quarter and before

    #     Returns:
    #         DataSelector: with the extracted data from the report
    #     """
    #     # Download reports for each quarter and update records for tickers specified
    #     download_list = Sec._getDownloadList(years, last_report)
    #     collector = DataSetCollector(self.download_manager)
    #     data = collector.getData(download_list)
    #     ticker_map = self.download_manager.getTickers()
    #     return DataSelector(data, ticker_map)
