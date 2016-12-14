#!/bin/bash -x

THIS_SCRIPT="$0";

cd "$(dirname ${THIS_SCRIPT})";

# cleanup any old build artifacts
rm -fr ./dist ./build;

# We should really be using a virtualenv for this, but unfortunately due to
# this bug:
# https://bitbucket.org/ronaldoussoren/py2app/issue/156/virtualenvpy-recipe-calls-methods-renamed#comment-None
# virtualenv-based py2app installations are presently failing.

# For the moment, on Travis, we just do everything in a homebrew Python
# installation.  Everywhere else, you can run this with PIP_USER=yes.

# install the stable dependencies for the main application
pip install -r requirements/production.txt;

# install the application itself
pip install .;

# install dependencies that are needed to build and run the mac application
pip install -r requirements/mac-app.txt;

# work around zope.interface's namespace module shenanigans
# see https://github.com/zopefoundation/zope.interface/issues/67
touch "$(dirname "$(dirname "$(python -c 'import zope.interface; print(zope.interface.__file__)')")")"/__init__.py

# build the application using py2app
python setup.py py2app;

# run the tests for application that py2app built
./dist/mimic.app/Contents/MacOS/run-tests;
