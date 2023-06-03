!!! warning "Experimental"
    This is not yet complete.

Calculate the F-Score. 

## Usage

```sh
base_command="python -m stocktracer analyze ${SMOKE_OPTIONS} --tickers aapl,msft,tmo,goog,googl,amzn,meta,acn,wm" 

echo "Running diluted_eps analysis..."
PYTHONPATH=src poetry run ${base_command} -a stocktracer.analysis.f_score --report-format=md --report-file=${results_dir}/diluted_eps.md
```

## Sample Output

```log
ticker,AAPL,ACN,AMZN,GOOG,GOOGL,META,MSFT,TMO,WM
fy,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0,2022.0
ROA>0,1,1,1,1,1,1,1,1,1
NetIncome>0,1,1,1,1,1,1,1,1,1
delta-ROA>0,1,1,0,1,1,0,1,0,1
CF/Total-Assets>ROA,1,1,1,1,1,1,1,1,1
debt-to-assets<last-year,0,0,0,0,0,0,0,0,0
current-ratio>last-year,0,0,0,0,0,0,0,0,0
shares-issued==0,0,1,0,0,0,1,1,0,0
```