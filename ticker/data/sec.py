from zipfile import ZipFile
from diskcache import Cache
from datetime import date
from pathlib import Path
import pandas as pd


class ReportDate:

    def __init__(self,
                 year: int = date.today().year,
                 quarter: int = ((date.today().month-1) / 3) + 1):
        if year > date.today().year:
            raise ValueError(
                "you cannot request reports in the future...that would be illegal :)")
        if not quarter in range(1, 4):
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


class Sec:

    # Format of zip example: 2023q1.zip
    _base_url = 'https://www.sec.gov/files/dera/data/financial-statement-data-sets/'

    _company_tickers_url = 'https://www.sec.gov/files/company_tickers.json'

    data: pd.DataFrame = None

    def __init__(self, storage_path: Path):
        if not isinstance(storage_path, Path):
            raise ValueError("storage_path is required")
        storage_path.mkdir(parents=True, exist_ok=True)
        self.storage_path = storage_path

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
        clk_map = self._updateCikMappings()

        # Download reports for each quarter and update records for tickers specified
        download_list = Sec._getDownloadList(years, last_report)
        for dl in download_list:
            self._updateQuarter(dl, clk_map)
        return self.data

    def _updateQuarter(self, report_archive: str, clk_map: pd.DataFrame) -> None:
        """ Update the quarter using the provided archive

        Args:
            report_archive (str): name of the zip file to download with the extension
            clk_map (pd.DataFrame): Map of CLK values to the stock ticker
        """
        # Make download request (if-needed based on file-cache)
        self._downloadArchive(report_archive)

        # Process Quarter (if needed - based on cache)
        return self._processArchive(report_archive, clk_map)

    def _updateCikMappings(self) -> pd.DataFrame:
        """update the CIK ticker mappings. This must be done before processing reports

        The SEC stores the mappings of the CIK values to tickers in a JSON file.
        We can download and cache this information essentially for a year. We're 
        not interested in companies that recently listed because they don't have a 
        long regulated record of reported earnings. When we process the records, we can 
        ignore cik values that are not in this list.


        Typical json for these looks like the following (without spaces or line breaks):

        {"0":{"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."},
         "1":{"cik_str":789019,"ticker":"MSFT","title":"MICROSOFT CORP"},

        Returns:
            pd.DataFrame: maps cik to stock ticker

        """
        # TODO: Make a cache request to _company_tickers_url
        return pd.DataFrame()

    def _getDownloadList(years: int, last_report: ReportDate) -> list[str]:
        """ Get a list of files to download for all the quarters.

        The list generated will include an extra quarter so that you will always be
        able to do analysis from the current quarter to the previous quarter.

        >>> Sec._getDownloadList(1, ReportDate(2023,2))
        ['2023q2.zip', '2023q1.zip', '2022q4.zip', '2022q3.zip', '2022q2.zip']

        Args:
            years (int): number of years to go back in time.
            last_report (ReportDate): only retrieve reports from this quarter and before

        Returns:
            list[str]: _description_
        """
        dl_list = list()
        next_report = last_report
        final_report = ReportDate(last_report.year-years, last_report.quarter)
        while 1:
            dl_list.append(f"{next_report.year}q{next_report.quarter}.zip")
            if next_report == final_report:
                break
            if 1 == next_report.quarter:
                next_report.quarter = 4
                next_report.year -= 1
            else:
                next_report.quarter -= 1
        return dl_list

    def _downloadArchive(self, report_archive: str) -> None:
        """_summary_

        Args:
            report_archive (str): name of the file w/ extension to be downloaded
        """
        # TODO: determine download agent
        pass

    def _processArchive(self, report_archive: str, clk_map: pd.DataFrame) -> None:
        """ Opens and extracts relevant data from a zip file archive

        Args:
            report_archive (str): name of the file w/ extension that was downloaded
            clk_map (pd.DataFrame): Map of CLK values to the stock ticker
        """
        arch_path = self._getArchiveStoragePath(report_archive)

        with ZipFile(arch_path) as myzip:
            # Process the mapping first
            with myzip.open('sub.txt') as myfile:
                # TODO: Process with pandas and filter the columns & rows
                # print(myfile.read())
                report_list = pd.read_csv(myfile)

                # TODO: Get reports that are 10-K or 10-Q

                with myzip.open('num.txt') as myfile:
                    # TODO: Process with pandas and filter the columns & rows
                    # print(myfile.read())
                    data_set = pd.read_csv(myfile)
                    # TODO: Filter out the results containing only those reports
                    # TODO: Store or merge with existing data

    def _getArchiveStoragePath(self, report_archive: str) -> Path:
        return self.storage_path / report_archive
