#!/usr/bin/env bash

MODULENAME="barnum"

docker build -t ${MODULENAME} .

docker run \
    -v "$(pwd)/input":/mnt/input \
    -v "$(pwd)/output":/mnt/output \
    --rm -it ${MODULENAME}
