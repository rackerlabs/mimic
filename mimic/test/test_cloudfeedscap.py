"""
Tests for :obj:`mimic.rest.cloudfeedscap`
"""
from __future__ import print_function

from mimic.rest.cloudfeedscap import generate_feed_xml

from twisted.trial.unittest import SynchronousTestCase


class GenFeedTests(SynchronousTestCase):
    """
    Tests for :func:`generate_feed`
    """

    def test_no_entries(self):
        print(generate_feed_xml([]))

    def test_entries(self):
        pass
