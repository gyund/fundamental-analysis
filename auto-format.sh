#!/bin/bash

dir=`dirname $0`

pushd $dir > /dev/null
ruff check --fix .
black ticker/ tests/
isort ticker/ tests/
pydoctest --config pydocktest.json
popd > /dev/null