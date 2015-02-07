#!/bin/bash

set -e
set -x

if [[ "${MACAPP_ENV}" == "system" ]]; then
    ./build-app.sh
else
    source ~/.venv/bin/activate
    tox -e $TOX_ENV
fi
