import pandas as pd
from ticker.cli import Options, ReportOptions
from ticker.data.sec import DataSelector as SecDataSelector
from ticker.filter import Entry
import logging
logger = logging.getLogger(__name__)

def analyze(options: Options):
    print("This is where we would start to process information, but we're not right now")

def report(options: ReportOptions):
    print("This is where we would report our findings, but we're not right now")
