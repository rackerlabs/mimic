#!/bin/bash

# clean out any previous artificats from py2app builds
find . -name 'dist' -print0 | xargs rm -rf
find . -name 'build' -print0 | xargs rm -rf

# build the application
python setup.py py2app

# run the the application's tests
./dist/mimic.app/Contents/MacOS/run-tests
