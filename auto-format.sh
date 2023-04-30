#!/bin/bash

dir=`dirname $0`

pushd $dir > /dev/null
ruff check --fix .
pydoctest --config pydocktest.json
popd > /dev/null