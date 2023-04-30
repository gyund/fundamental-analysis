from pathlib import Path
import os
import importlib


class Options:
    def __init__(self, tickers: list[str], cache_path: Path):
        self.tickers = tickers
        self.cache_path = cache_path


class ReportOptions(Options):
    def __init__(self, file: Path = None, json: Path = None, **kwargs):
        super().__init__(**kwargs)
        self.file = file
        self.json = json


class Cli:

    """Tools for gathering resources, analyzing data, and publishing the results."""

    default_analysis_module = "ticker.analysis.stub"

    def getDefaultCachePath() -> Path:
        """Get the default path for caching data

        Returns:
            Path: path to cache data
        """
        return Path(os.getcwd()) / ".ticker-cache"

    def analyze(
        self,
        tickers: list[str],
        cache_path: Path = getDefaultCachePath(),
        analysis_plugin: str = default_analysis_module,
    ) -> None:
        """Perform stock analysis

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path where to cache data
            analysis_plugin (str): module to load for analysis
        """
        # Call analysis plugin
        analysis_module = importlib.import_module(analysis_plugin)
        options = Options(tickers=tickers, cache_path=cache_path)
        analysis_module.analyze(options)

    def export(
        self,
        tickers: list[str],
        cache_path: Path = getDefaultCachePath(),
        file: Path = None,
        json: Path = None,
        analysis_plugin: str = default_analysis_module,
    ) -> None:
        """Create a report in one of the following formats based on data already analyzed

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path of cached data
            file (Path): text file containing the report. Defaults to None.
            json (Path): directory to store the reports in individual json files. Defaults to None.
            analysis_plugin (str): module to load for analysis
        """
        # Call analysis plugin
        analysis_module = importlib.import_module(analysis_plugin)
        options = ReportOptions(
            tickers=tickers, cache_path=cache_path, file=file, json=json
        )
        analysis_module.report(options)
