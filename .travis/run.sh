#!/bin/bash

set -e
set -x

source ~/.venv/bin/activate

case "${BUNDLE_ENV}" in
    system)
        ./build-app.sh
        ;;
    *)
    	tox -e $TOX_ENV
        ;;
esac
