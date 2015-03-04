#!/bin/bash -x

THIS_SCRIPT="$0";

cd "$(dirname ${THIS_SCRIPT})";

# cleanup any old build artifacts
rm -fr ./dist ./build;

# We should really be using a virtualenv for this, but unfortunately due to
# this bug:
# https://bitbucket.org/ronaldoussoren/py2app/issue/156/virtualenvpy-recipe-calls-methods-renamed#comment-None
# virtualenv-based py2app installations are presently failing.  So, for the
# moment, we require --user installations of everything.

# Travis seems to have an old setuptools that results in version conflict
# exceptions.
pip install --upgrade pip==6.0.8;
pip install --upgrade setuptools==12.3;

# install the dependencies for the main application
pip install -r requirements.txt;

# install the application itself
pip install .;

# install dependencies that are needed to build and run the mac application
pip install -r py2app-requirements.txt;

# This _really_ should have been installed by now
pip install six==1.6.1;

# build the application using py2app
python setup.py py2app;

# run the tests for application that py2app built
./dist/mimic.app/Contents/MacOS/run-tests;
