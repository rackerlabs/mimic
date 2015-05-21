"""
Unit tests for :mod:`mimic.util`
"""
from twisted.trial.unittest import SynchronousTestCase
from twisted.web.resource import Resource

from mimic.util import helper
from mimic.test.helpers import request


class HelperTests(SynchronousTestCase):
    """
    Tests for :mod:`mimic.util.helper`
    """

    matches = [(0, "1970-01-01T00:00:00.000000Z"),
               (1.5, "1970-01-01T00:00:01.500000Z"),
               (121.4005, "1970-01-01T00:02:01.400500Z")]

    def _validate_ipv4_address(self, address, *prefixes):
        nums = [int(x) for x in address.split('.')]
        self.assertEqual(4, len(nums))
        self.assertTrue(all(x >= 0 and x < 256 for x in nums))
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

    def test_random_hex_generator(self):
        """
        A completely random and unique hex encoded data is generated.
        """
        self.assertNotEqual(helper.random_hex_generator(3),
                            helper.random_hex_generator(3))
        self.assertEqual(len(helper.random_hex_generator(4)), 8)

    def test_seconds_to_timestamp_default_timestamp(self):
        """
        :func:`helper.seconds_to_timestamp` returns a timestamp matching
        the seconds since the epoch given.  The timestamp conforms to with the
        default format string of ``%Y-%m-%dT%H:%M:%S.%fZ`` if no format
        string is provided.
        """
        for seconds, timestamp in self.matches:
            self.assertEqual(timestamp, helper.seconds_to_timestamp(seconds))

    def test_seconds_to_timestamp_provided_timestamp(self):
        """
        :func:`helper.seconds_to_timestamp` uses the provided timestamp format
        to format the seconds.
        """
        formats = [("%m-%d-%Y %H:%M:%S", "01-01-1970 00:00:00"),
                   ("%Y-%m-%d", "1970-01-01"),
                   ("%H %M %S (%f)", "00 00 00 (000000)")]
        for fmt, timestamp in formats:
            self.assertEqual(timestamp,
                             helper.seconds_to_timestamp(0, fmt))

    def test_timestamp_to_seconds(self):
        """
        :func:`helper.timestamp_to_seconds` returns a seconds since EPOCH
        matching the corresponding timestamp given in ISO8601 format
        """

        local_matches = [(0, "1970-01-01"), (0, "1970-01-01T00"),
                         (0, "1970-01-01T00:00"), (1800, "1970-01-01T00-00:30")]
        for seconds, timestamp in self.matches + local_matches:
            self.assertEqual(seconds, helper.timestamp_to_seconds(timestamp))


class TestHelperTests(SynchronousTestCase):
    """
    Tests for :obj:`mimic.test.helpers`.
    """

    def test_unicode_body(self):
        """
        If :obj:`request` is given a unicode request body, the deferred
        synchronously fails so that the caller can immediately tell something
        is wrong.
        """
        self.failureResultOf(
            request(self, Resource(), b"POST", b"", u"not bytes")
        )


class TestRandomString(SynchronousTestCase):
    """
    Tests for random string generation.
    """

    def test_length(self):
        """
        The random string you generate should have the length you specify.
        """
        for l in range(100):
            self.assertEqual(len(helper.random_string(l)), l)

    def test_selectable(self):
        """
        When passing a custom selectable, the results should derive only from
        the characters you provide.
        """
        desired_chars = "02468"
        for iteration in xrange(100):
            a_string = helper.random_string(1024, selectable=desired_chars)
            for char in a_string:
                self.assertTrue(char in desired_chars)
