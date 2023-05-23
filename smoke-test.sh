#!/bin/bash

SMOKE_OPTIONS=${SMOKE_OPTIONS:="--refresh"}

dir=`dirname $0`
results_dir='.results'
set -e

pushd ${dir} > /dev/null
mkdir -p ${results_dir}
echo "Running default analysis..."
PYTHONPATH=src pipenv run python -m stocktracer analyze ${SMOKE_OPTIONS} --tickers aapl,msft,tmo,goog,googl,amzn,meta,acn,wm --report-format=csv  > ${results_dir}/default.csv

echo "Running diluted_eps analysis..."
PYTHONPATH=src pipenv run python -m stocktracer analyze ${SMOKE_OPTIONS} --tickers aapl,msft,tmo -a stocktracer.analysis.diluted_eps --report-format=md --report-file=${results_dir}/diluted_eps.md

popd > /dev/null