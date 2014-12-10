#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from sys import argv
from twisted.scripts.trial import run

argv[1:] = ["mimic"]
run()
