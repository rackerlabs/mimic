"""
start_app.py starts the application for py2app.

This calls twistd with default arguments.
"""

from mimic.tap import Options, makeService
from sys import argv
from twisted.scripts.twistd import run

argv[1:] = [
    'mimic'
]

run()
