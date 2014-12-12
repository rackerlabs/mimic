#!/usr/bin/env python
"""
run the tests for the mimic.aplication bundle.
"""
import sys

from twisted.trial.runner import (
    TestLoader,
    TrialRunner
)
from twisted.trial.reporter import VerboseTextReporter

# in order to find the app-bundle, the site-packages.zip
# file needs to be added to path.
sys.path.insert(0, b'./lib/python/site-packages.zip')

from mimic import test


def runTests():
    """
    run tests from the mimic module.
    """
    loader = TestLoader()
    suite = loader.loadAnything(test)
    runner = TrialRunner(VerboseTextReporter).run(suite)


if __name__ == '__main__':
    runTests()
