#!/bin/bash

# cleanup any old build artifacts
find . -name 'dist' -print0 | xargs rm -rf
find . -name 'build' -print0 | xargs rm -rf

if [[ ! -d ./venv-app ]]; then
    virtualenv ./venv-app -p /usr/bin/python2.7 --system-site-packages
fi

source  ./venv-app/bin/activate

# install the dependencies for the main application
pip install -r requirements.txt
# the test bundle needs to unittest2
pip install "unittest2>=0.5.1"
# build the application using py2app
python setup.py py2app
# run the tests for application py2app built
./dist/mimic.app/Contents/MacOS/run-tests
