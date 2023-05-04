#!/bin/bash

dir=`dirname $0`

pushd $dir > /dev/null
ruff check --fix .
black src/
isort src/
pydoctest --config pydocktest.json
popd > /dev/null