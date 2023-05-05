import abc
from pathlib import Path
from pandas import DataFrame


class Options:
    def __init__(self, tickers: frozenset[str], cache_path: Path):
        self.tickers = tickers
        self.cache_path = cache_path


class ReportOptions:
    def __init__(self, results, file: Path = None, json: Path = None, **kwargs):
        self.results = results
        self.file = file
        self.json = json


class Analysis(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def analyze(self) -> DataFrame:
        pass

    @property
    def options(self) -> Options:
        if self._options is None:
            return Options()
        return self._options

    @options.setter
    def options(self, options: Options):
        self._options = options
