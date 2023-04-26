import pandas as pd


class Analysis:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def analyze(self, tickers: list[str]):
        pass

    def report(self, tickers: list[str]):
        pass
