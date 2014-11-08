"""
start_app.py starts the application for py2app.

This calls twistd with default arguments.
"""

from os.path import join, dirname
from sys import argv
from twisted.scripts.twistd import run

# pass the name of the application - this fills argv.
argv[1:] = [
    'mimic'
]

# this will start the application
run()
