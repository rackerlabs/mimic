#!/usr/bin/env python

from sys import argv
from twisted.scripts.trial import run
# you should import the test module and run it programmatically!
# don't do any other form of discovery.

argv[1:] = [
    'mimic'
]
run()
