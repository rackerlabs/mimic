#!/bin/bash

set -e
set -x

if [[ "${TOX_ENV}" == "bundle" ]]; then
    virtualenv ~/.venv2 -p /usr/local/bin/python2.7
    source ~/.venv2/bin/activate
    pip install -r requirements.txt
    pip install -r dev-requirements.txt
    pip install -r py2app-requirements.txt
    make build
    make test
else
    source ~/.venv/bin/activate
    tox -e $TOX_ENV -- $TOX_FLAGS
fi
