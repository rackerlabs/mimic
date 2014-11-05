"""
Unit tests for :mod:`mimic.util`
"""

from twisted.trial.unittest import SynchronousTestCase

from mimic.util import helper


class HelperTests(SynchronousTestCase):
    """
    Tests for :mod:`mimic.util.helper`
    """
    def _validate_ipv4_address(self, address, *prefixes):
        nums = [int(x) for x in address.split('.')]
        self.assertEqual(4, len(nums))
        self.assertTrue(all(x > 0 and x < 255 for x in nums))
        self.assertEqual(prefixes[:len(nums)], tuple(nums[:len(prefixes)]))

    def test_random_ipv4_completely_random(self):
        """
        A completely random IP address is generated if prefixes are not
        provided.
        """
        self._validate_ipv4_address(helper.random_ipv4())

    def test_random_ipv4_with_prefixes(self):
        """
        Random IP addresses can be generated with pre-determined prefixes.
        """
        prefixes = []
        for i in range(1, 5):
            prefixes.append(i)
            self._validate_ipv4_address(helper.random_ipv4(*prefixes),
                                        *prefixes)
