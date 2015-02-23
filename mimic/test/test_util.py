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
        matches = [(0, "1970-01-01T00:00:00.000000Z"),
                   (1.5, "1970-01-01T00:00:01.500000Z"),
                   (121.4005, "1970-01-01T00:02:01.400500Z")]
        for match in matches:
            self.assertEqual(match[1], helper.seconds_to_timestamp(match[0]))

    def test_seconds_to_timestamp_provided_timestamp(self):
        """
        :func:`helper.seconds_to_timestamp` uses the provided timestamp format
        to format the seconds.
        """
        matches = [("%m-%d-%Y %H:%M:%S", "01-01-1970 00:00:00"),
                   ("%Y-%m-%d", "1970-01-01"),
                   ("%H %M %S (%f)", "00 00 00 (000000)")]
        for match in matches:
            self.assertEqual(match[1],
                             helper.seconds_to_timestamp(0, match[0]))


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

    def test_bad_request(self):
        """
        ``bad_request`` provides a well-formed error body for HTTP errors.

        The ``illegal_response`` function constructs a hash with a message and
        HTTP response code, for the convenience of expressing error details in
        JSON format.  However, it doesn't provide the full envelop expected by
        Nova clients.
        """
        d = helper.bad_request("The cake is a lie.", 404)
        self.assertTrue(d.get("badRequest", None))
        self.assertEqual(d["badRequest"]["code"], 404)
        self.assertEqual(d["badRequest"]["message"], "The cake is a lie.")
