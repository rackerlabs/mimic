#!/usr/bin/env python
"""
run the tests for the mimic.application bundle.
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


def run_tests():
    """
    Run all of mimics tests.
    """
    loader = TestLoader()
    suite = loader.loadPackage(test)
    runner = TrialRunner(VerboseTextReporter).run(suite)


if __name__ == '__main__':
    run_tests()
