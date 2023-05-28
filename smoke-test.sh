#!/bin/bash

SMOKE_OPTIONS=${SMOKE_OPTIONS:="--refresh"}

dir=`dirname $0`
results_dir='.results'
set -e

pushd ${dir} > /dev/null
mkdir -p ${results_dir}

base_command="python -m stocktracer analyze --tickers aapl,msft,tmo,goog,googl,amzn,meta,acn,wm"

echo "Running default analysis..."
PYTHONPATH=src pipenv run ${base_command} --report-format=csv  > ${results_dir}/default.csv

echo "Running f-score analysis..."
PYTHONPATH=src pipenv run ${base_command} --report-format=csv -a stocktracer.analysis.f_score  > ${results_dir}/fscore.csv

echo "Running diluted_eps analysis..."
PYTHONPATH=src pipenv run ${base_command} -a stocktracer.analysis.diluted_eps --report-format=md --report-file=${results_dir}/diluted_eps.md



popd > /dev/null