!!! warning "Experimental"

This analysis module grabs the annual reports and data associated data.

## Usage

```sh
base_command="python -m stocktracer analyze ${SMOKE_OPTIONS} --tickers aapl,msft,tmo,goog,googl,amzn,meta,acn,wm" 

echo "Running default analysis..."
PYTHONPATH=src poetry run ${base_command} --report-format=csv  > ${results_dir}/default.csv
```

## Sample Output

```log
ticker,AAPL,ACN,AMZN,GOOG,GOOGL,META,MSFT,TMO,WM
fy,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0
tag,,,,,,,,,
AccountsPayableCurrent,59439000000.0,2416771000.0,79132000000.0,5582500000.0,5582500000.0,,17081500000.0,3124000000.0,1570500000.0
AccountsPayableOtherCurrent,,,,,,1084500000.0,,,
AccountsPayableTradeCurrent,,,,,,4536500000.0,,,
AccountsReceivableAllowanceForCreditLossOther,,,,,,,,,-6000000.0
```