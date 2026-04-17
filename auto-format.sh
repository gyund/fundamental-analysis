#!/bin/bash

dir=`dirname $0`
PYLINT_FLAG=${PYLINT_FLAG:=""}

# Stop script on first failure
set -e

pushd $dir > /dev/null
echo "Running auto-format tools..."
hatch run ruff check --fix .
hatch run isort src/
hatch run black src/

echo "Running pydoctest..."
PYTHONPATH=src hatch run pydoctest --config pydocktest.json

# Note: false positivies in the src/test from fixtures, etc.
echo "Running pylint..."
hatch run pylint ${PYLINT_FLAG} src/stocktracer
echo "Running pydocstyle... (not required to pass)"
hatch run pydocstyle || echo "warnings - see above for recommendations"
echo "success!"
popd > /dev/null