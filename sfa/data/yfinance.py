from source import Source as DataSource

class YFinance(DataSource):
    def __init__(self):
       pass

DataSource.register(YFinance)