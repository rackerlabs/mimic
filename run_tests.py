#!/usr/bin/env python

from sys import argv
from twisted.scripts.trial import run

argv[1:] = ["../mimic"]
run()
