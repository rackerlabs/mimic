#!/bin/bash

if [[ ! -d ./.build-venv ]]; then
    virtualenv ./.build-venv -p /usr/bin/python2.7 --system-site-packages
fi

source  ./.build-venv/bin/activate
pip freeze

pip install -r requirements.txt
pip install -r dev-requirements.txt
pip install -r py2app-requirements.txt

find . -name 'dist' -print0 | xargs rm -rf
find . -name 'build' -print0 | xargs rm -rf

# build the application
python setup.py py2app

# run the the application's tests
./dist/mimic.app/Contents/MacOS/run-tests
