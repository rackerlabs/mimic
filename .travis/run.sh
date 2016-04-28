#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == "Darwin" ]]; then
    eval "$(pyenv init -)"
fi

if [[ "${MACAPP_ENV}" == "system" ]]; then
    ./build-app.sh;
    exit "$?";
fi;

source ~/.venv/bin/activate;

ls .wheels;
PIP_FIND_LINKS="$(pwd)/.wheels" PIP_NO_INDEX=yes tox --recreate --develop -- $TOX_FLAGS;
