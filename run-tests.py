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


def runTests():
    """
    run tests from the mimic module.
    """
    sys.path.insert(0, b'./lib/python/site-packages.zip')
    from mimic import test

    loader = TestLoader()
    suite = loader.loadAnything(test)
    runner = TrialRunner(VerboseTextReporter).run(suite)

if __name__ == '__main__':
    runTests()
