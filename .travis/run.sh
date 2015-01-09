#!/bin/bash

set -e
set -x

source ~/.venv/bin/activate

if [[ "$(uname -s)" == "Darwin" ]]; then

    # run tox for all but bundle.
    if [[ "${TOX_ENV}" == 'bundle' ]]; then
        pip install -r requirements.txt
        pip install -r dev-requirements.txt
        pip install -r py2app-requirements.txt
        make
    else
        # run the tests for a single env
        tox -e $TOX_ENV
    fi
else
    # I realize this is ugly.
    tox -e $TOX_ENV
fi
