import pandas as pd
from ticker.cli import Options, ReportOptions
from ticker.data.sec import DataSelector as SecDataSelector
from ticker.filter import Selectors,SecFilter
import logging
logger = logging.getLogger(__name__)

def analyze(options: Options) -> None:
    """ Analyze the report

    As a stub, this does nothing

    Args:
        options (Options): options to use for processing
    """    
    print("This is where we would start to process information, but we're not right now")

def report(options: ReportOptions) -> None:
    """ Generate a report

    As a stub, this does nothing, but normally it provides a mechanism
    to customize the report generated from the analysis phase.

    This allows you to keep processed data in a intermediary format and create reports from
    already processed data without having to do it again.

    Args:
        options (ReportOptions): Reporting options to use for processing
    """    
    print("This is where we would report our findings, but we're not right now")
