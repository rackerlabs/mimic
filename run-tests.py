#!/usr/bin/env python

import sys

from mimic import test

from twisted.trial.runner import (
    TestLoader,
    TrialRunner
)
from twisted.trial.reporter import VerboseTextReporter

# XXX this works as a normal script, but in the package
# it is unable to discover the tests.
def runTests():
    """
    run tests from the mimic module.
    """
    loader = TestLoader()
    suite = loader.loadPackage(test)
    runner = TrialRunner(VerboseTextReporter).run(suite)


if __name__ == '__main__':
    runTests()
