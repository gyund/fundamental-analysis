from ticker.data.source import Source, Stub
from ticker.data.yfinance import YFinance

class Cli:
    """Tools for gathering resources, analyzing data, and publishing the results."""

    def analyze(self, source: str) -> None:
        """ Perform stock analysis

        Args:
            source (str): adapter to use, options include: yfinance, stub
        """        
        if not source:
            source = self._default_source()
        
        adapter = self._getSourceAdapter(source)
        

    def export(self, source: str, file :str = None, json :str = None ) -> None:
        """ Create a report in one of the following formats based on data already analyzed

        Args:
            source (str): adapter to use, options include: yfinance, stub
            file (str): text file containing the report. Defaults to None.
            json (str): directory to store the reports in individual json files. Defaults to None.
        """               
        pass

    def _default_source(self) -> str:
        """ [Default data source to use if not specified]

        Returns:
            str: default source to use
        """
        return "yfinance"
    
    def _getSourceAdapter(self, adapter_name: str) -> Source:
        """Get the object representing the specified data source

        Args:
            adapter_name (str): valid types include: yfinance, stub

        Raises:
            ValueError: the adapter_name was not valid

        Returns:
            Source: adapter providing the data
        """        
        
        if not isinstance(adapter_name, str):
            raise ValueError("adapter-type is invalid")
        match(adapter_name):
            case "yfinance":
                return YFinance()
            case "stub":
                return Stub()
            case _: 
                raise ValueError("invalid adapter-type specified")