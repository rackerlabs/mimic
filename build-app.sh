#!/bin/bash

THIS_SCRIPT="$0";

cd "$(dirname ${THIS_SCRIPT})";

# cleanup any old build artifacts
rm -fr ./dist ./build;

# We should really be using a virtualenv for this, but unfortunately due to
# this bug:
# https://bitbucket.org/ronaldoussoren/py2app/issue/156/virtualenvpy-recipe-calls-methods-renamed#comment-None
# virtualenv-based py2app installations are presently failing.  So, for the
# moment, we require --user installations of everything.

# install the dependencies for the main application
pip install --user -r requirements.txt;

# install dependencies that are needed to build and run the mac application
pip install --user -r py2app-requirements.txt;

# build the application using py2app
python setup.py py2app;

# run the tests for application that py2app built
./dist/mimic.app/Contents/MacOS/run-tests;
