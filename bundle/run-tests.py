"""
run the tests for the mimic.application bundle.
"""

import sys

from twisted.trial.runner import (
    TestLoader,
    TrialRunner
)
from twisted.trial.reporter import VerboseTextReporter
from twisted.plugin import getPlugins, IPlugin

# in order to find the app-bundle, the site-packages.zip
# file needs to be added to path.
sys.path.insert(0, b'./lib/python/site-packages.zip')

from mimic import test


def runTests():
    """
    Run all of mimics tests.
    """
    loader = TestLoader()
    suite = loader.loadPackage(test)
    passFail = not TrialRunner(VerboseTextReporter).run(suite).wasSuccessful()
    sys.exit(passFail)


if __name__ == '__main__':
    runTests()
