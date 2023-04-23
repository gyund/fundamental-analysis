from abc import ABCMeta, abstractmethod

class Source(metaclass=ABCMeta):
    """Interface for data retrieval"""    

    @abstractmethod
    def getCashFlowFromOperatingActivities(self, ticker: str) -> int:
        """ Get cash flow from operating activities

        Args:
            ticker (str): ticker symbol

        Returns:
            int: cash flow
        """        
        pass
    

class Stub(Source):
    """Stub for the data source."""
    
    def getCashFlowFromOperatingActivities(self, ticker: str) -> int:
        """get cash flow from operating activities

        Args:
            ticker (str): stock ticker

        Returns:
            int: 0 
        """        
        return 0
