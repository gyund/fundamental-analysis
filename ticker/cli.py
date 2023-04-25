from ticker.data.sec import Sec
from pathlib import Path
import os

class Cli:

    """Tools for gathering resources, analyzing data, and publishing the results."""

    def analyze(self, 
                tickers : list[str], 
                cache_path : Path = Path(os.getcwd()) / ".ticker-cache") -> None:
        """ Perform stock analysis

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path where to cache data
        """
        self._doUpdateFromSec(tickers, cache_path)

        # TODO: Call analysis plugin

    def _doUpdateFromSec(self, tickers : list[str], cache_path : Path):
        sec = Sec(storage_path=Path(cache_path))

        sec.update(tickers=tickers)

    def export(self, tickers : list[str], 
               cache_path : Path = Path(os.getcwd()) / ".ticker-cache",
               file: Path = None, 
               json: Path = None) -> None:
        """ Create a report in one of the following formats based on data already analyzed

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path of cached data
            file (Path): text file containing the report. Defaults to None.
            json (Path): directory to store the reports in individual json files. Defaults to None.
        """
        pass
