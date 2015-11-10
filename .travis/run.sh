#!/bin/bash

set -e
set -x

# Use pyenv if pyenv is installed and available.
if PY_ENV="$(pyenv init -)"; then
    eval "${PY_ENV}";
fi

if [[ "${MACAPP_ENV}" == "system" ]]; then
    ./build-app.sh
else
    source ~/.venv/bin/activate
    tox --develop -- $TOX_FLAGS
fi
