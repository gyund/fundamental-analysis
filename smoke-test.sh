#!/bin/bash

SMOKE_OPTIONS=${SMOKE_OPTIONS:="--final-year=2023 --final-quarter=1"}

dir=`dirname $0`
results_dir='docs/.smoke-tests'
set -e

pushd ${dir} > /dev/null
mkdir -p ${results_dir}

base_command="python -m stocktracer analyze ${SMOKE_OPTIONS} --tickers aapl,msft,tmo,goog,googl,amzn,meta,acn,wm" 
PYTHONPATH=src

echo "Running default analysis..."
cmd="poetry run ${base_command} --report-format=csv"
echo "PYTHONPATH=src ${cmd} > ${results_dir}/default.csv" > ${results_dir}/default.cmd
${cmd} > ${results_dir}/default.csv

echo "Running f-score analysis..."
cmd="poetry run ${base_command} --report-format=csv -a stocktracer.analysis.f_score"
echo "PYTHONPATH=src ${cmd} > ${results_dir}/fscore.csv" > ${results_dir}/fscore.cmd
${cmd} > ${results_dir}/fscore.csv

echo "Running diluted_eps analysis..."
cmd="poetry run ${base_command} -a stocktracer.analysis.diluted_eps --report-format=md --report-file=${results_dir}/diluted_eps.md"
echo "PYTHONPATH=src ${cmd}" > ${results_dir}/diluted_eps.cmd
${cmd}

echo "Running tensorflow analysis..."
cmd="poetry run ${base_command} -a stocktracer.analysis.tensorflow"
echo "PYTHONPATH=src ${cmd} > ${results_dir}/tensorflow.txt" > ${results_dir}/tensorflow.cmd
${cmd} > ${results_dir}/tensorflow.txt

popd > /dev/null