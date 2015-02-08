#!/bin/bash

# cleanup any old build artifacts
find . -name 'dist' -print0 | xargs rm -rf
find . -name 'build' -print0 | xargs rm -rf

if [[ ! -d ./venv-app ]]; then
    virtualenv ./venv-app -p /usr/bin/python2.7 --system-site-packages
fi

source  ./venv-app/bin/activate

pip install -r requirements.txt
pip install "unittest2>=0.5.1"

python setup.py py2app

./dist/mimic.app/Contents/MacOS/run-tests
