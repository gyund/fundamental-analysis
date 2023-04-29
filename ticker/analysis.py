import pandas as pd
from ticker.data.sec import DataSelector as SecDataSelector


class Analysis:
    def __init__(self, data: SecDataSelector):
        self.secData = data

    def analyze(self, tickers: list[str]):
        pass

    def report(self, tickers: list[str]):
        pass
