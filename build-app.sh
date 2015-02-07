#!/bin/bash
rm -rf ./build
rm -rf ./dist
python setup.py py2app
./dist/mimic.app/Contents/MacOS/run-tests
