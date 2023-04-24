from diskcache import Cache
from datetime import date

class ReportDate:

    def __init__(self, year = date.today().year, quarter = ((date.today().month-1) / 3) + 1) -> None:
        """_summary_

        Args:
            year (int): _description_. Defaults to date.today().year.
            quarter (int): _description_. Defaults to ((date.today().month-1) / 4)+1.
        """
        if year > date.today().year:
            raise ValueError("you cannot request reports in the future...that would be illegal :)")
        if not quarter in range(1,4):
            raise ValueError("the value for the quarter must be a value between 1 and 4")
        pass

class Sec:
    
    # Format of zip example: 2023q1.zip
    _base_url = 'https://www.sec.gov/files/dera/data/financial-statement-data-sets/'

    def update(self, tickers: list, years: int = 5, last_report : ReportDate = ReportDate()) -> None:
        """ Update the database with information about the following stocks.

        When this command runs, it will pull updates starting from 

        Args:
            tickers (list): only store and catalog information about these tickers
            years (int): number of years to go back in time. Defaults to 5.
            last_report (ReportDate): only retrieve reports from this quarter and before
        """
        # Download reports for each quarter and update records for tickers specified
        download_list = self._getDownloadList(years, last_report)
        for dl in download_list:
            self._updateQuarter(dl)
            pass
        

    def _updateQuarter(self, report_archive: str):
        """ Update the quarter using the provided archive

        Args:
            report_archive (str): name of the zip file to download with the extension
        """
        # Make download request (if-needed based on file-cache)
        # TODO: determine download agent

        # Unzip request (if-needed)

        # Process Quarter (if needed - based on cache)

        pass

    def _getDownloadList(years: int, last_report : ReportDate) -> list[str]:
        """ Get a list of files to download for all the quarters.

        The list generated will include an extra quarter so that you will always be
        able to do analysis from the current quarter to the previous quarter.

        >>> Sec._getDownloadList(1, ReportDate(2023,2))
        ['2023q2.zip','2023q1.zip','2022q4.zip','2022q3.zip','2022q2.zip']

        Args:
            years (int): number of years to go back in time.
            last_report (ReportDate): only retrieve reports from this quarter and before

        Returns:
            list[str]: _description_
        """            
        pass
