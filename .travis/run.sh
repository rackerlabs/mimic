#!/bin/bash

set -e
set -x

source ~/.venv/bin/activate

if [[ "${MACAPP_ENV}" == "system" ]]; then
        ./build-app.sh
else
    	tox -e $TOX_ENV
fi
