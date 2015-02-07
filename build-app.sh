#!/bin/bash
find . -name 'dist' -print0 | xargs rm -rf
find . -name 'build' -print0 | xargs rm -rf
python setup.py py2app
./dist/mimic.app/Contents/MacOS/run-tests
