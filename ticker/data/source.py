from abc import ABCMeta, abstractmethod

class Source(ABCMeta):
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
    

