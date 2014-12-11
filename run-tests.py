#!/usr/bin/env python

import sys

from twisted.trial.runner import (
    TestLoader,
    TrialRunner
)
from twisted.trial.reporter import VerboseTextReporter
from mimic import test

def runTests():
    """
    run tests.
    """
    loader = TestLoader()
    suite = loader.loadTestsFromModule(test)
    # reporter factory
    runner = TrialRunner(VerboseTextReporter).run(suite)


if __name__ == '__main__':
    runTests()
