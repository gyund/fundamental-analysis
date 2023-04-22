#!/bin/bash

dir=`dirname $0`

pushd $dir > /dev/null
ruff check --fix .
popd > /dev/null