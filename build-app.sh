#!/bin/bash

# cleanup any old build artifacts
find . -name 'dist' -print0 | xargs rm -rf
find . -name 'build' -print0 | xargs rm -rf

# build a virtualenv which will be used for all of the application's
# dependencies if one doesn't already exist
if [[ ! -d ./venv-app ]]; then
    virtualenv ./venv-app -p /usr/bin/python2.7 --system-site-packages
fi

source  ./venv-app/bin/activate

# install the dependencies for the main application
pip install -r requirements.txt

# install dependencies that are needed to build and run the mac application
pip install -r py2app-requirements.txt

# build the application using py2app
python setup.py py2app

# run the tests for application that py2app built
./dist/mimic.app/Contents/MacOS/run-tests
