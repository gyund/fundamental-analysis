"""This data source grabs information from quarterly SEC data archives."""
import copy
import logging
import sys
from datetime import date
from io import BytesIO
from typing import Literal, Optional
from zipfile import ZipFile

import numpy as np
import pandas as pd
from alive_progress import alive_bar
from beartype import beartype
from beartype.typing import Callable, Sequence
from numpy.linalg import LinAlgError

from stocktracer import cache

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1000000
pd.set_option("mode.chained_assignment", "raise")


@beartype
class ReportDate:
    """ReportDate is used to select and identify archives created by the SEC."""

    def __init__(
        self,
        year: int | None = None,
        quarter: int | None = None,
    ):
        """

        Args:
            year (int, optional): Year of the archive. Defaults to date.today().year.
            quarter (int, optional): Quarter the archive was created. Defaults to ((date.today().month - 1) // 3)+1.

        Raises:
            ValueError: If the value for quarter or year is invalid
        """
        self.year = date.today().year if year is None else year
        self.quarter = (
            ((date.today().month - 1) // 3) + 1 if quarter is None else quarter
        )

        if self.year > date.today().year:
            raise ValueError(
                "you cannot request reports in the future...that would be illegal :)"
            )
        if self.quarter not in range(1, 5):
            raise ValueError(
                f"the quarter must be a value between 1 and 4 - given: {quarter}"
            )

    def __str__(self) -> str:
        return f"{self.year}-q{self.quarter}"

    def __repr__(self) -> str:
        return f"ReportDate({self.year},{self.quarter})"

    def __eq__(self, other: "ReportDate") -> bool:
        return self.quarter == other.quarter and self.year == other.year


@beartype
class TickerReader:
    """This class provides translation services for CIK and Ticker values.

    The SEC has a `json` file that provides mappings from CIK values to Tickers.
    The data providing this conversion is injected into this class and then
    this class provides helper methods for performing the conversion on this data set.

    This class is provided CSV data which is parsed upon initialization. So creating
    this object is the most expensive part.
    """

    def __init__(self, data: str):
        self._cik_to_ticker_map = pd.read_json(data, orient="index")

    @property
    def map_of_cik_to_ticker(self) -> pd.DataFrame:
        """Dataframe containing mapping of cik and ticker information.

        Returns:
            pd.DataFrame: Dataframe with mapping information
        """
        return self._cik_to_ticker_map

    def convert_to_cik(self, ticker: str) -> np.int64:
        """Get the Cik from the stock ticker.

        Args:
            ticker (str): stock ticker. The case does not matter.

        Raises:
            LookupError: If ticker is not found

        Returns:
            np.int64: cik
        """
        result = self.map_of_cik_to_ticker[
            self.map_of_cik_to_ticker["ticker"] == ticker.upper()
        ]
        if result.empty:
            raise LookupError(f"unable to find ticker: {ticker}")
        return result.cik_str.iloc[0]

    def convert_to_ticker(self, cik: int) -> str:
        """Get the stock ticker from the Cik number.

        Args:
            cik (int): Cik number for the stock

        Returns:
            str: stock ticker
        """
        result = self.map_of_cik_to_ticker[self.map_of_cik_to_ticker["cik_str"] == cik]
        return result.ticker.iloc[0]

    def contains(self, tickers: frozenset) -> bool:
        """Check that the tickers provided exist.

        Args:
            tickers (frozenset): tickers to check

        Returns:
            bool: if all the tickers are found
        """
        for ticker in tickers:
            self.convert_to_cik(ticker)

        return True


@beartype
def slope(data: pd.Series, order: int = 1) -> float:
    """Calculate the trend of a series.

    >>> import math
    >>> math.isclose(slope(pd.Series((1,2,3))), 1)
    True

    >>> math.isclose(slope(pd.Series((3,2,1))), -1)
    True

    Args:
        data (pd.Series): _description_
        order (int): _description_. Defaults to 1.

    Returns:
        float: slope of the trend line
    """
    x_axis = range(len(data.keys()))
    y_axis = data.values

    try:
        coeffs = np.polyfit(x_axis, y_axis, order)
    except LinAlgError:
        return float(0)
    return coeffs[0]


@beartype
class Filter:
    """Filter for SEC tools to scrape relevant information when processing records."""

    class Results:
        """This is the results from a `Filter.select()` call.

        The results table looks like the following:

        ```
        tag            AccountsPayableCurrent  ...  WeightedAverageNumberOfSharesOutstandingBasic
        ticker fy                              ...
        AAPL   2021.0            4.852950e+10  ...                                   1.750824e+10
               2022.0            5.943900e+10  ...                                   1.675645e+10
        MSFT   2021.0            1.384650e+10  ...                                   7.610000e+09
               2022.0            1.708150e+10  ...                                   7.551000e+09
        TMO    2021.0            2.521000e+09  ...                                   3.966667e+08
               2022.0            3.124000e+09  ...                                   3.940000e+08
        ```

        From here, you can call functions on this class like `get_value()` or `normalize()`.

        !!! note
            To get a list of all the tags, run the `annual_reports` analysis module and search through the output for meaningful tags.

        """

        def __init__(self, results: pd.DataFrame) -> None:
            logger.debug(f"results:\n{results}")
            self.data = results

        def __str__(self) -> str:
            return str(self.data)

        @property
        def tags(self) -> np.ndarray:
            """List of tags that can be used on this data set.

            Returns:
                np.ndarray: array with results
            """
            return self.data.columns.values

        def get_value(self, ticker: str | int, tag: str, year: int) -> int | float:
            """Retrieve the exact value of a table cell.

            Args:
                ticker (str | int): ticker identifying the equity of interest.
                tag (str): attribute indicating the type of data to look at.
                year (int): The year this data applies to.

            Returns:
                int | float: value of result
            """
            # Lookup convert ticker to cik
            ticker = ticker.upper()
            return self.data.loc[ticker].loc[year].loc[tag]

        def normalize(self):
            """Remove all values that are NaN."""
            self.data = self.data.dropna(axis=1, how="any")

        def slice(
            self,
            ticker: Optional[str | int] = None,
            year: Optional[int] = None,
            tags: Optional[list[str]] = None,
        ) -> pd.DataFrame:
            """Slice the results by the specified values

            Args:
                ticker (Optional[str  |  int]): _description_. Defaults to None.
                tags (Optional[str]): _description_. Defaults to None.
                year (Optional[int]): _description_. Defaults to None.

            Returns:
                pd.DataFrame: _description_
            """
            result = self.data
            if ticker:
                result = result.loc(axis=0)[ticker, :]
            if year:
                result = result.loc(axis=0)[:, year, :]
            if tags:
                result = pd.DataFrame(result.loc[:, tags], columns=tags)
            return result

        def calculate_net_income(self, column_name: str):
            """Calculates the net income stocks as a series.

            !!! example
                ``` python
                results.calculate_net_income()
                ```

            Args:
                column_name (str): name to assign to the column
            """
            self.data[column_name] = self.data["OperatingIncomeLoss"]

        def calculate_current_ratio(self, column_name: str):
            """Calculate the current ratio.

            The current ratio is a liquidity ratio that measures a company’s
            ability to pay short-term obligations or those due within one year.

            Args:
                column_name (str): _description_
            """
            self.data[column_name] = (
                self.data["AssetsCurrent"] / self.data["LiabilitiesCurrent"]
            )

        def calculate_debt_to_assets(self, column_name: str):
            """Calculates the current debt to assets ratio.

            Having more debt than assets is a risk indicator that could indicate
            a potential for bankruptcy.

            Args:
                column_name (str): name to assign to the column
            """
            self.data[column_name] = (
                self.data["LiabilitiesCurrent"] / self.data["AssetsCurrent"]
            )

        def calculate_return_on_assets(self, column_name: str):
            """Returns the ROA of stocks as a series.

            !!! example
                ``` python
                results.calculate_return_on_assets('ROA')
                ```
            Args:
                column_name (str): name to assign to the column
            """
            self.data[column_name] = self.data["OperatingIncomeLoss"].div(
                self.data["Assets"]
            )

        def calculate_delta(self, column_name: str, delta_of: str):
            """Calculate the change between the latest row and the one before it within a ticker.

            Args:
                column_name (str): name to give the calculated column
                delta_of (str): column name to calculate the delta of, such as ROI
            """
            self.data[column_name] = self.data.groupby(by=["ticker"]).diff()[delta_of]

    def __init__(
        self,
        tags: Optional[list[str]] = None,
        years: int = 1,
        last_report: ReportDate = ReportDate(),
        only_annual: bool = True,
    ) -> None:
        """

        This is an important concept to dealing with large data sets. It allows us to chunk processing
        into batches and find/locate only records of interest. Without these filters, the tool would
        require absurd amounts of memory and storage to process.

        Args:
            tags (Optional[list[str]]): list of tags found in the SEC report, such as 'EntityCommonStockSharesOutstanding'
            years (int): years of reports desired. Defaults to 1.
            last_report (ReportDate): most recent SEC data dump identified by the year an quarter. Defaults to ReportDate().
            only_annual (bool): If true, only scrape the annual reports. Defaults to True.
        """
        self.tags = tags
        self.years = years
        self.last_report = last_report
        self.only_annual = only_annual
        self._cik_list: Optional[set[np.int64]] = None
        self._filtered_data: Optional[pd.DataFrame] = None

    @property
    def filtered_data(self) -> Optional[pd.DataFrame]:
        """Filtered data looks like this(in csv format):

        Note that fp has the "Q" removed from the front so it can be stored as a simple number.

        .. code-block:: text

            ticker,tag,fy,fp,ddate,uom,value,period,title
            AAPL,EntityCommonStockSharesOutstanding,2022,Q1,2023-01-31,shares,2000.0,2022-12-31,Apple Inc.
            AAPL,FakeAttributeTag,2022,Q1,2023-01-31,shares,200.0,2022-12-31,Apple Inc.

        Returns:
            Optional[pd.DataFrame]: _description_
        """
        return self._filtered_data

    @filtered_data.setter
    def filtered_data(self, filtered_data: pd.DataFrame):
        self._filtered_data = filtered_data

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

    def select(
        self,
        aggregate_func: Optional[
            Callable | Literal["mean", "std", "var", "sum", "min", "max", "slope"]
        ] = "mean",
        tickers: Optional[Sequence[str]] = None,
    ) -> Results:
        """Select only a subset of the data matching the specified criteria.

        Args:
            aggregate_func (Optional[Callable | Literal['mean', 'std', 'var', 'sum', 'min','max','slope']]): Numpy function to use for aggregating the results. This should be a function like `numpy.average` or `numpy.sum`.
            tickers (Optional[Sequence[str]]): ticker symbol for the company

        Returns:
            Filter.Results: Object that represents a pivot table with the data requested
        """
        assert self.filtered_data is not None
        if tickers is not None:
            tickers = [t.upper() for t in tickers]
            logger.debug(f"ticker filter: {tickers}")

        data = (
            self.filtered_data
            if tickers is None
            else self.filtered_data.query("ticker in @tickers")
        )
        logger.debug(f"pre-pivot:\n{data}")

        # Try and see if the function exists
        if isinstance(aggregate_func, str):
            if aggregate_func in globals():
                aggregate_func = globals()[aggregate_func]

        table: pd.DataFrame = pd.pivot_table(
            data,
            values="value",
            columns="tag",
            index=["ticker", "fy"],
            aggfunc=aggregate_func,
        )

        return Filter.Results(table)

    @property
    def ciks(self) -> set[np.int64]:
        """Retrieves a list of CIK values corresponding to the tickers being looked up.

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

    def populate_ciks(
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
            cik = ticker_reader.convert_to_cik(ticker)
            self._cik_list.add(cik)

    @property
    def focus_period(self) -> list[str]:
        """Get the focus period for the report.

        Companies file quarterly reports. The annual report replaces the quarterly
        report depending on when that is reported. Typically Q4 is replaced with FY
        for the annual reports.

        Returns:
            list[str]: list of focus periods to use for the filter
        """
        if self.only_annual:
            return ["FY"]
        return ["FY", "Q1", "Q2", "Q3", "Q4"]

    @property
    def required_reports(self) -> list[ReportDate]:
        """Get a list of required reports to download for all the quarters.

        The list generated will include an extra quarter so that you will always be
        able to do analysis from the current quarter to the previous quarter.

        Also note that it doesn't matter if you specify only_annual=True. Because
        companies don't have the same fiscal year, we have to check every quarterly
        report just to see if their annual report is in there.

        Returns:
            list[ReportDate]: list of report dates to retrieve
        """
        dl_list: list[ReportDate] = []
        next_report = copy.deepcopy(self.last_report)
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
    """Reads the data from a zip file retrieved from the SEC website."""

    def __init__(self, zip_data: bytes) -> None:
        self.zip_data = BytesIO(zip_data)

    def process_zip(self, sec_filter: Filter) -> Optional[pd.DataFrame]:
        """Process a zip archive with the provided filter.

        Args:
            sec_filter (Filter): results to filter out of the zip archive

        Raises:
            ImportError: the filter doesn't match anything

        Returns:
            Optional[pd.DataFrame]: filtered data
        """
        with ZipFile(self.zip_data) as myzip:
            # Process the mapping first
            logger.debug("opening sub.txt")
            with myzip.open("sub.txt") as myfile:
                # Get reports that are 10-K or 10-Q
                sub_dataframe = DataSetReader._process_sub_text(myfile, sec_filter)

                if sub_dataframe is None or sub_dataframe.empty:
                    raise ImportError("nothing found in sub.txt matching the filter")

                with myzip.open("num.txt") as myfile:
                    return DataSetReader._process_num_text(
                        myfile, sec_filter, sub_dataframe
                    )

    @classmethod
    def _process_num_text(
        cls, filepath_or_buffer, sec_filter: Filter, sub_dataframe: pd.DataFrame
    ) -> Optional[pd.DataFrame]:
        """Contains the numerical data.

        adsh	tag	version	coreg	ddate	qtrs	uom	value	footnote

        """
        logger.debug("processing num.txt")
        reader = pd.read_csv(
            filepath_or_buffer,
            delimiter="\t",
            usecols=["adsh", "tag", "ddate", "uom", "value"],
            index_col=["adsh", "tag"],
            chunksize=DEFAULT_CHUNK_SIZE,
            parse_dates=["ddate"],
        )

        filtered_data: Optional[pd.DataFrame] = None
        chunk: pd.DataFrame
        for chunk in reader:
            # We want only the tables in left if they join on the key, so inner it is
            data = chunk.join(sub_dataframe, how="inner")

            # Additional Filtering if needed
            if sec_filter.tags is not None:
                tag_list = sec_filter.tags  # pylint: disable=unused-variable
                data = data.query("tag in @tag_list")

            if data.empty:  # pragma: no cover
                # logger.debug(f"chunk:\n{chunk}")
                # logger.debug(f"sub_dataframe:\n{sub_dataframe}")
                continue

            filtered_data = cls.append(filtered_data, data)

        # if filtered_data is not None:  # pragma: no cover
        #     logger.debug(f"Filtered Records (head+5): {filtered_data.head()}")
        return filtered_data

    @classmethod
    def append(
        cls, filtered_data: Optional[pd.DataFrame], data: pd.DataFrame
    ) -> pd.DataFrame:
        """Append data to the filtered_data and return the updated filtered DataFrame.

        >>> df1 = pd.DataFrame({"A": ["A0", "A1", "A2", "A3"]},index=[0,1,2,3])
        >>> df2 = pd.DataFrame({"B": ["B0", "B1", "B2", "B3"]},index=[4,5,6,7])
        >>> DataSetReader.append(df1, df2)
             A    B
        0   A0  NaN
        1   A1  NaN
        2   A2  NaN
        3   A3  NaN
        4  NaN   B0
        5  NaN   B1
        6  NaN   B2
        7  NaN   B3
        >>> DataSetReader.append(None, df1)
            A
        0  A0
        1  A1
        2  A2
        3  A3
        >>> DataSetReader.append(df1, df1)
            A
        0  A0
        1  A1
        2  A2
        3  A3
        0  A0
        1  A1
        2  A2
        3  A3

        Args:
            filtered_data (Optional[pd.DataFrame]): Existing Data
            data (pd.DataFrame): New data

        Returns:
            pd.DataFrame: Filtered Data
        """
        if filtered_data is None:
            filtered_data = data
        else:
            filtered_data = pd.concat([filtered_data, data])
        return filtered_data

    @classmethod
    def _process_sub_text(
        cls, filepath_or_buffer, sec_filter: Filter
    ) -> Optional[pd.DataFrame]:
        """Contains the submissions.

        adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma
        stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi
        fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
        """
        logger.debug("processing sub.txt")
        focus_periods = sec_filter.focus_period
        cik_list = sec_filter.ciks  # pylint: disable=unused-variable

        oldest_fy = sec_filter.last_report.year - sec_filter.years
        query_str = f"cik in @cik_list and fp in @focus_periods and fy >= {oldest_fy}"
        # logger.debug(f"Query string: {query_str}")
        reader = pd.read_csv(
            filepath_or_buffer,
            delimiter="\t",
            usecols=["adsh", "cik", "period", "fy", "fp"],
            index_col=["adsh", "cik"],
            chunksize=DEFAULT_CHUNK_SIZE,
            parse_dates=["period"],
            dtype={"cik": np.int32},
        )
        logger.info(f"keeping only these focus periods: {focus_periods}")
        filtered_data: Optional[pd.DataFrame] = None
        chunk: pd.DataFrame
        for chunk in reader:
            data = chunk.query(query_str)
            if data.empty:
                continue
            filtered_data = cls.append(filtered_data, data)
        return filtered_data


@beartype
class DownloadManager:
    """This class is responsible for downloading and caching downloaded data sets from the SEC."""

    # Format of zip example: 2023q1.zip
    _base_url = "https://www.sec.gov/files/dera/data/financial-statement-data-sets"

    _company_tickers_url = "https://www.sec.gov/files/company_tickers.json"

    @property
    def ticker_reader(self) -> TickerReader:
        """Get the CIK ticker mappings. This must be done before processing reports.

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
        response = cache.sec_tickers.get(self._company_tickers_url)
        if response.from_cache:  # pragma: no cover
            logger.info("Retrieved tickers->cik mapping from cache")
        if response.status_code == 200:  # pragma: no cover
            return TickerReader(response.content.decode())
        raise LookupError("unable to retrieve tickers")  # pragma: no cover

    def _create_download_uri(self, report_date: ReportDate) -> str:
        file = f"{report_date.year}q{report_date.quarter}.zip"
        return "/".join([self._base_url, file])

    def get_quarterly_report(self, report_date: ReportDate) -> Optional[DataSetReader]:
        """Retrieve from a cache or make a request archived quarterly data.

        This allows us to download data independent of actually processing it, allowing
        us to prefetch information we need if we like.

        Args:
            report_date (ReportDate): information specifying the quarterly dump to retrieve

        Returns:
            Optional[DataSetReader]: this object helps process the data received more granularly
        """
        request = self._create_download_uri(report_date)
        response = cache.sec_data.get(request)
        if response.from_cache:
            logger.info(f"Retrieved {request} from cache")

        if response.status_code == 200:
            return DataSetReader(response.content)
        return None  # pragma: no cover


@beartype
class DataSetCollector:
    """Take care of downloading all the data sets and aggregate them into a single structure."""

    def __init__(self, download_manager: DownloadManager):
        self.download_manager = download_manager

    def get_data(self, sec_filter: Filter) -> None:
        """Collect data based on the provided filter.

        Args:
            sec_filter (Filter): SEC specific filter of how to filter the results

        Raises:
            LookupError: when there are no results matching the filter

        """
        data_frame = None
        report_dates = sec_filter.required_reports
        logger.info(f"Creating Unified Data record for these reports: {report_dates}")
        with alive_bar(
            # total=len(report_dates) * 2,
            theme="smooth",
            # stats=False,
            title="Records Retrieved",
            file=sys.stderr,
            calibrate=5_000,
            dual_line=True,
        ) as status_bar:
            for report_date in report_dates:
                status_bar.text(f"Downloading report {report_date}...")
                reader = self.download_manager.get_quarterly_report(report_date)
                if isinstance(reader, DataSetReader):
                    try:
                        status_bar.text(f"Processing report {report_date}...")
                        data = reader.process_zip(sec_filter)
                        if data_frame is not None:
                            logger.debug(f"record count: {len(data_frame)}")
                        if data is not None:
                            logger.debug(f"new record count: {len(data)}")
                            data_frame = DataSetReader.append(data_frame, data)
                            record_count = len(data_frame)
                            status_bar(record_count)  # pylint: disable=not-callable
                            logger.info(
                                f"There are now {record_count} filtered records"
                            )

                    except ImportError:
                        # Note, when searching for annual reports, this will generally occur 1/4 times
                        # if we're only searching for one stock's tags
                        logger.debug(
                            f"{report_date} did not have any matches for the provided filter"
                        )
                        logger.debug(f"{sec_filter}")

        logger.info(f"Created Unified Data record for these reports: {report_dates}")
        if data_frame is None:
            raise LookupError("No data matching the filter was retrieved")

        # Now add an index for ticker values to pair with the cik
        # logger.debug(f"filtered_df_before_merge:\n{data_frame.to_csv()}")
        data_frame = data_frame.reset_index().merge(
            right=self.download_manager.ticker_reader.map_of_cik_to_ticker,
            how="inner",
            left_on="cik",
            right_on=["cik_str"],
        )

        # Columns at this point look like this
        #  ,adsh,tag,cik,ddate,uom,value,period,fy,fp,cik_str,ticker,title
        # 0,0000097745-23-000008,EarningsPerShareDiluted,97745,2022-12-31,USD,17.63,2022-12-31,2022.0,FY,97745,TMO,THERMO FISHER SCIENTIFIC INC.
        # 1,0000097745-23-000008,EarningsPerShareDiluted,97745,2020-12-31,USD,15.96,2022-12-31,2022.0,FY,97745,TMO,THERMO FISHER SCIENTIFIC INC.
        # 2,0000097745-23-000008,EarningsPerShareDiluted,97745,2021-12-31,USD,19.46,2022-12-31,2022.0,FY,97745,TMO,THERMO FISHER SCIENTIFIC INC..

        sec_filter.filtered_data = data_frame.drop(
            columns=["cik_str", "adsh", "cik"]
        ).set_index(["ticker", "tag", "fy", "fp"])

        # # Convert fp to number so we can sort easily
        # data_frame['fp'].mask(data_frame['fp'] == "Q1", 1, inplace=True)
        # data_frame['fp'].mask(data_frame['fp'] == "Q2", 2, inplace=True)
        # data_frame['fp'].mask(data_frame['fp'] == "Q3", 3, inplace=True)
        # data_frame['fp'].mask(data_frame['fp'] == "Q4", 4, inplace=True)
        # data_frame = data_frame.set_index("fp", append=True)

        # logger.debug(f"filtered_df:\n{data_frame}")
        # filter.filtered_data = data_frame


@beartype
class Sec:
    """Object for handling requests for information relating to SEC data dumps."""

    def __init__(self):
        self.download_manager = DownloadManager()

    @cache.results.memoize(typed=True, expire=60 * 60 * 24 * 7, tag="sec")
    def filter_data(self, tickers: frozenset[str], sec_filter: Filter) -> Filter:
        """Initiate the retrieval of ticker information based on the provided filters.

        Filtered data is stored with the filter

        Args:
            tickers (frozenset[str]): ticker symbols you want information about
            sec_filter (Filter): SEC specific data to scrape from the reports

        Returns:
            Filter: filter with filtered data
        """
        self.filter_data_nocache(tickers, sec_filter)

    def filter_data_nocache(
        self, tickers: frozenset[str], sec_filter: Filter
    ) -> Filter:
        """Same as filter_data but no caching is applied.

        Args:
            tickers (frozenset[str]): _description_
            sec_filter (Filter): _description_

        Returns:
            Filter: _description_
        """
        collector = DataSetCollector(self.download_manager)
        ticker_reader = self.download_manager.ticker_reader
        if ticker_reader.contains(tickers):
            sec_filter.populate_ciks(tickers=tickers, ticker_reader=ticker_reader)
            collector.get_data(sec_filter)

        return sec_filter
