#!/bin/bash

set -e
set -x

source ~/.venv/bin/activate
if [[ "${TOX_ENV}" == "bundle" ]]; then
    pip install -r requirements.txt
    pip install -r dev-requirements.txt
    pip install -r py2app-requirements.txt
    make build
    make test
else
    tox -e $TOX_ENV -- $TOX_FLAGS
fi
