#!/bin/bash

dir=`dirname $0`

pushd $dir > /dev/null
ruff -v --format=github --select=E9,F63,F7,F82 --target-version=py37 . --fix
popd > /dev/null