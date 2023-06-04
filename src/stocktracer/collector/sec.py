"""This data source grabs information from quarterly SEC data archives."""
import copy
import logging
import sys
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from typing import Literal, Optional
from zipfile import ZipFile

import numpy as np
import pandas as pd
from alive_progress import alive_bar
from beartype import beartype
from beartype.typing import Callable, Sequence

from stocktracer import cache

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 200000
pd.set_option("mode.chained_assignment", "raise")


@beartype
@dataclass(frozen=True)
class ReportDate:
    """ReportDate is used to select and identify archives created by the SEC."""

    year: int = date.today().year
    quarter: int = ((date.today().month - 1) // 3) + 1

    def __post_init__(self):
        if self.year > date.today().year:
            raise ValueError(
                "you cannot request reports in the future...that would be illegal :)"
            )
        if self.quarter not in range(1, 5):
            raise ValueError(
                f"the quarter must be a value between 1 and 4 - given: {self.quarter}"
            )

    def __str__(self) -> str:
        return f"{self.year}-q{self.quarter}"


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

    def get_ciks(self, tickers: frozenset[str]) -> frozenset[int]:
        """Populates the filter's CIK list to be used for filtering.

        The Filter doesn't need the ticker symbols. If we expand to other data sources,
        we would have to repeat ticker symbols. For now, the only info we need in the
        report is the CIK values to find the corresponding stocks.

        Args:
            tickers (frozenset[str]): ticker symbols to search for

        Returns:
            frozenset[int]: CIKs values translated from the tickers specified
        """
        cik_list: set[int] = set()
        for ticker in tickers:
            cik = self.convert_to_cik(ticker)
            cik_list.add(int(cik))
        return frozenset(cik_list)


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
        # An exception can be thrown if there's only one element of it's a nan
        coeffs = np.polyfit(x_axis, y_axis, order)
    except np.linalg.LinAlgError:
        return float(0)
    except Exception as e:
        logger.warning(f"slope exception: {e}")
        return float(0)
    return coeffs[0]


@beartype
@dataclass(frozen=True)
class Filter:
    """Filter for SEC tools to scrape relevant information when processing records."""

    years: int = field(hash=True)
    tags: Optional[list[str]] = field(default=None, hash=True)
    last_report: ReportDate = field(default=ReportDate(), hash=True)
    only_annual: bool = field(default=True, hash=True)

    @property
    def focus_period(self) -> frozenset[str]:
        """Get the focus period for the report.

        Companies file quarterly reports. The annual report replaces the quarterly
        report depending on when that is reported. Typically Q4 is replaced with FY
        for the annual reports.

        Returns:
            frozenset[str]: list of focus periods to use for the filter
        """
        if self.only_annual:
            return frozenset({"FY"})
        return frozenset({"FY", "Q1", "Q2", "Q3", "Q4"})

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
                next_report = ReportDate(year=next_report.year - 1, quarter=4)
            else:
                next_report = ReportDate(
                    year=next_report.year, quarter=next_report.quarter - 1
                )
        return dl_list


@beartype
@dataclass
class Results:
    """Filtered data looks like this(in csv format):

    Note that fp has the "Q" removed from the front so it can be stored as a simple number.

    .. code-block:: text

        ticker,tag,fy,fp,ddate,uom,value,period,title
        AAPL,EntityCommonStockSharesOutstanding,2022,Q1,2023-01-31,shares,2000.0,2022-12-31,Apple Inc.
        AAPL,FakeAttributeTag,2022,Q1,2023-01-31,shares,200.0,2022-12-31,Apple Inc.
    """

    filtered_data: pd.DataFrame

    _cik_list: Optional[set[np.int64]] = None

    @beartype
    @dataclass
    class Table:
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

        data: pd.DataFrame

        def __str__(self) -> str:
            return str(self.data)

        @property
        def tags(self) -> np.ndarray:
            """List of tags that can be used on this data set.

            Returns:
                np.ndarray: array with results
            """
            return self.data.columns.values

        def get_value(self, ticker: str, tag: str, year: int) -> int | float:
            """Retrieve the exact value of a table cell.

            Args:
                ticker (str): ticker identifying the equity of interest.
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
            ticker: Optional[str | list[str]] = None,
            year: Optional[int] = None,
            tags: Optional[list[str]] = None,
        ) -> pd.DataFrame:
            """Slice the results by the specified values

            Args:
                ticker (Optional[str | list[str]]): _description_. Defaults to None.
                tags (Optional[str]): _description_. Defaults to None.
                year (Optional[int]): _description_. Defaults to None.

            Returns:
                pd.DataFrame: _description_
            """
            result = self.data
            if ticker:
                if isinstance(ticker, str):
                    ticker = ticker.upper()
                else:
                    ticker = [t.upper() for t in ticker]
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

    def select(
        self,
        aggregate_func: Optional[
            Callable | Literal["mean", "std", "var", "sum", "min", "max", "slope"]
        ] = "mean",
        tickers: Optional[Sequence[str]] = None,
    ) -> Table:
        """Select only a subset of the data matching the specified criteria.

        Args:
            aggregate_func (Optional[Callable | Literal['mean', 'std', 'var', 'sum', 'min','max','slope']]): Numpy function to use for aggregating the results. This should be a function like `numpy.average` or `numpy.sum`.
            tickers (Optional[Sequence[str]]): ticker symbol for the company

        Returns:
            Results.Table: Object that represents a pivot table with the data requested
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

        return Results.Table(table)

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


@beartype
@dataclass(frozen=True)
class DataSetReader:
    """Reads the data from a zip file retrieved from the SEC website."""

    request_uri: str

    def process_zip(
        self, sec_filter: Filter, ciks: frozenset[int]
    ) -> Optional[pd.DataFrame]:
        """Process a zip archive with the provided filter.

        Args:
            sec_filter (Filter): results to filter out of the zip archive
            ciks (frozenset[int]): CIKs to filter data on

        Returns:
            Optional[pd.DataFrame]: filtered data
        """
        zip_data = cache.sec_data.get(self.request_uri, only_if_cached=True)
        if zip_data is None:
            raise LookupError(f"missing cache entry for request: {self.request_uri}")

        with ZipFile(BytesIO(zip_data.content)) as myzip:
            # Process the mapping first
            logger.debug("opening sub.txt")
            with myzip.open("sub.txt") as myfile:
                # Get reports that are 10-K or 10-Q
                sub_dataframe = DataSetReader._process_sub_text(
                    myfile, sec_filter, ciks
                )

                if sub_dataframe is None or sub_dataframe.empty:
                    logger.debug("nothing found in sub.txt matching the filter")
                    return None

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

        filtered_data = cls._process_num_serial(sec_filter, sub_dataframe, reader)

        # if filtered_data is not None:  # pragma: no cover
        #     logger.debug(f"Filtered Records (head+5): {filtered_data.head()}")
        return filtered_data

    @classmethod
    def _process_num_serial(cls, sec_filter, sub_dataframe, reader):
        """Process num.txt in a single thread (serial fashion)."""
        filtered_data: Optional[pd.DataFrame] = None
        chunk: pd.DataFrame

        for chunk in reader:
            data = cls._process_num_chunk(sec_filter, sub_dataframe, chunk)
            if data.empty:  # pragma: no cover
                # logger.debug(f"chunk:\n{chunk}")
                # logger.debug(f"sub_dataframe:\n{sub_dataframe}")
                continue
            filtered_data = cls.append(filtered_data, data)
        return filtered_data

    @classmethod
    def _process_num_chunk(cls, sec_filter, sub_dataframe, chunk):
        # We want only the tables in left if they join on the key, so inner it is
        data = chunk.join(sub_dataframe, how="inner")

        # Additional Filtering if needed
        if sec_filter.tags is not None:
            tag_list = sec_filter.tags  # pylint: disable=unused-variable
            data = data.query("tag in @tag_list")
        return data

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
        cls,
        filepath_or_buffer,
        sec_filter: Filter,
        ciks: frozenset[int],  # pylint: disable=unused-argument
    ) -> Optional[pd.DataFrame]:
        """Contains the submissions.

        adsh	cik	name	sic	countryba	stprba	cityba	zipba	bas1	bas2	baph	countryma
        stprma	cityma	zipma	mas1	mas2	countryinc	stprinc	ein	former	changed	afs	wksi
        fye	form	period	fy	fp	filed	accepted	prevrpt	detail	instance	nciks	aciks
        """
        logger.debug("processing sub.txt")
        focus_periods = sec_filter.focus_period

        oldest_fy = sec_filter.last_report.year - sec_filter.years
        query_str = f"cik in @ciks and fp in @focus_periods and fy >= {oldest_fy}"
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
            return DataSetReader(request)
        return None  # pragma: no cover


download_manager = DownloadManager()


@beartype
class DataSetCollector:
    """Take care of downloading all the data sets and aggregate them into a single structure."""

    def get_data(self, sec_filter: Filter, ciks: frozenset[int]) -> Results:
        """Collect data based on the provided filter.

        Args:
            sec_filter (Filter): SEC specific filter of how to filter the results
            ciks (frozenset[int]): CIK values to filter the datasets on

        Raises:
            LookupError: when the filter returned no matches

        Returns:
            Results: filtered data results

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
            funclist: list[Future] = []

            with ProcessPoolExecutor() as executor:
                for report_date in report_dates:
                    reader = download_manager.get_quarterly_report(report_date)

                    if reader is None:
                        raise ImportError(f"missing quarterly report for {report_date}")

                    future = executor.submit(
                        _process_report_task, sec_filter, ciks, reader
                    )
                    funclist.append(future)

                for f in funclist:
                    data = f.result(timeout=60)  # timeout in 60 seconds

                    if data is None:
                        # Note, when searching for annual reports, this will generally occur 1/4 times
                        # if we're only searching for one stock's tags
                        continue

                    if data_frame is not None:
                        logger.debug(f"record count: {len(data_frame)}")

                    logger.debug(f"new record count: {len(data)}")
                    data_frame = DataSetReader.append(data_frame, data)
                    record_count = len(data_frame)
                    status_bar(record_count)  # pylint: disable=not-callable
                    logger.info(f"There are now {record_count} filtered records")

        logger.info(f"Created Unified Data record for these reports: {report_dates}")
        if data_frame is None:
            raise LookupError("No data matching the filter was retrieved")

        # Now add an index for ticker values to pair with the cik
        # logger.debug(f"filtered_df_before_merge:\n{data_frame.to_csv()}")
        data_frame = data_frame.reset_index().merge(
            right=download_manager.ticker_reader.map_of_cik_to_ticker,
            how="inner",
            left_on="cik",
            right_on=["cik_str"],
        )

        # Columns at this point look like this
        #  ,adsh,tag,cik,ddate,uom,value,period,fy,fp,cik_str,ticker,title
        # 0,0000097745-23-000008,EarningsPerShareDiluted,97745,2022-12-31,USD,17.63,2022-12-31,2022.0,FY,97745,TMO,THERMO FISHER SCIENTIFIC INC.
        # 1,0000097745-23-000008,EarningsPerShareDiluted,97745,2020-12-31,USD,15.96,2022-12-31,2022.0,FY,97745,TMO,THERMO FISHER SCIENTIFIC INC.
        # 2,0000097745-23-000008,EarningsPerShareDiluted,97745,2021-12-31,USD,19.46,2022-12-31,2022.0,FY,97745,TMO,THERMO FISHER SCIENTIFIC INC..

        return Results(
            data_frame.drop(columns=["cik_str", "adsh", "cik"]).set_index(
                ["ticker", "tag", "fy", "fp"]
            )
        )


def _process_report_task(
    sec_filter: Filter, ciks: frozenset[int], reader: DataSetReader
) -> Optional[pd.DataFrame]:
    """Task function for processing a single report."""

    return reader.process_zip(sec_filter, ciks)

    # # Convert fp to number so we can sort easily
    # data_frame['fp'].mask(data_frame['fp'] == "Q1", 1, inplace=True)
    # data_frame['fp'].mask(data_frame['fp'] == "Q2", 2, inplace=True)
    # data_frame['fp'].mask(data_frame['fp'] == "Q3", 3, inplace=True)
    # data_frame['fp'].mask(data_frame['fp'] == "Q4", 4, inplace=True)
    # data_frame = data_frame.set_index("fp", append=True)

    # logger.debug(f"filtered_df:\n{data_frame}")
    # filter.filtered_data = data_frame


@beartype
@cache.results.memoize(tag="sec")
def filter_data(
    tickers: list[str],
    sec_filter: Filter,
) -> Results:
    """Initiate the retrieval of ticker information based on the provided filters.

    Filtered data is stored with the filter

    Args:
        tickers (list[str]): ticker symbols you want information about
        sec_filter (Filter): SEC specific data to scrape from the reports

    Returns:
        Results: results with filtered data
    """
    logger.debug(f"tickers:\n{repr(tickers)}")
    logger.debug(f"sec_filter:\n{repr(sec_filter)}")
    return filter_data_nocache(frozenset(tickers), sec_filter)


def filter_data_nocache(tickers: frozenset[str], sec_filter: Filter) -> Results:
    """Same as filter_data but no caching is applied.

    Args:
        tickers (frozenset[str]): ticker symbols you want information about
        sec_filter (Filter): SEC specific data to scrape from the reports

    Returns:
        Results: results with filtered data
    """
    collector = DataSetCollector()
    ticker_reader = download_manager.ticker_reader

    # Returns true or throws
    ticker_reader.contains(tickers)

    ciks = ticker_reader.get_ciks(tickers=tickers)
    return collector.get_data(sec_filter, ciks)
