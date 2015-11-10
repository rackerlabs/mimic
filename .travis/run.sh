#!/bin/bash

set -e
set -x

# Use pyenv if pyenv is installed and available.

PY_ENV="$(pyenv init -)";

if [ -n "${PY_ENV}" ]; then
    eval "${PY_ENV}";
fi

if [[ "${MACAPP_ENV}" == "system" ]]; then
    ./build-app.sh
else
    source ~/.venv/bin/activate
    tox --develop -- $TOX_FLAGS
fi
