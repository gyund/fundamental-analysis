from abc import ABCMeta, abstractmethod

class Source(ABCMeta):
    def __init__(self):
       pass

    @abstractmethod
    def getCashFlowFromOperatingActivities(self, ticker: str) -> int:
        pass
    

