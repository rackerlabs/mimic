# -*- test-case-name: mimic.test.test_util -*-
#
"""
Helper methods

:var fmt: strftime format for datetimes used in JSON.
"""
import os
import string
import calendar
from datetime import datetime, timedelta
import json
from random import choice, randint

import iso8601

from six import text_type


fmt = '%Y-%m-%dT%H:%M:%S.%fZ'


EMPTY_RESPONSE = object()


def json_dump(o):
    """
    Serialize an object to JSON, unless it is :obj:`EMPTY_RESPONSE`, in which
    case the empty string will be returned.
    """
    if o is EMPTY_RESPONSE:
        return b''
    else:
        return json.dumps(o)


def random_string(length, selectable=None):
    """
    Create a random string of the specified length.

    :param int length: How long the string must be.
    :param str selectable: If left unspecified, the random character selection
        will be taken from uppercase and lowercase letters, digits, and a few
        punctuation marks.  Otherwise, the characters will be taken from the
        string provided.
    :returns: A string of length `length`.
    """
    selectable = (
        selectable or (string.letters + string.digits + string.punctuation)
    )
    return ''.join([choice(selectable) for _ in xrange(length)])


def random_hipsum(length):
    """
    Generates a random sentence using Hipsum ( http://hipsum.co/ ).

    :param length The number of words in the desired sentence.
    :returns: A Unicode string containing `length` words.
    """
    hipsum = ''.join([
        "Retro squid Portland raw denim Austin, normcore slow-carb Brooklyn. ",
        "Deep v organic VHS drinking vinegar. Fingerstache locavore kogi Tumblr ",
        "cred. Vice typewriter retro iPhone pour-over cred XOXO church-key, ",
        "post-ironic kogi. Selvage polaroid retro, cold-pressed meh craft beer ",
        "artisan pour-over taxidermy sartorial art party. Food truck church-key ",
        "four loko wayfarers craft beer dreamcatcher normcore yr, jean shorts ",
        "bespoke migas art party crucifix next level. Street art chia bitters, ",
        "gastropub mixtape flexitarian Godard occupy lumbersexual."]).split(' ')
    offset = randint(1, len(hipsum))
    rotated = hipsum[offset:] + hipsum[:offset]
    return ' '.join(rotated[:length])


def random_ipv4(*numbers):
    """
    Return a random IPv4 address - parts of the IP address can be provided.
    For example, ``random_ipv4(192, 168)`` will return a random 192.168.x.x
    address.
    """
    all_numbers = [text_type(num) for num in
                   list(numbers) + [randint(0, 255) for _ in range(4)]]
    return ".".join(all_numbers[:4])


def random_hex_generator(num):
    """
    Returns randomly generated n bytes of encoded hex data for the given `num`
    """
    return os.urandom(num).encode("hex")


def seconds_to_timestamp(seconds, format=fmt):
    """
    Return an ISO8601 Zulu timestamp given seconds since the epoch.
    """
    return datetime.utcfromtimestamp(seconds).strftime(format)


def timestamp_to_seconds(timestamp):
    """
    Return epoch from an ISO8601 Zulu timestamp

    :param str timestamp: ISO8601 formatted time
    :return: EPOCH seconds
    :rtype: float
    """
    dt = iso8601.parse_date(timestamp)
    return calendar.timegm(dt.utctimetuple()) + dt.microsecond / 1000000.


def not_found_response(resource='servers'):
    """
    Return a 404 response body, depending on the resource.  Expects
    resource to be one of "images", "flavors", "loadbalancer", or "node".

    If the resource is unrecognized, defaults to
    "The resource culd not be found."
    """
    message = {
        'images': "Image not found.",
        'flavors': "The resource could not be found.",
        'loadbalancer': "Load balancer not found",
        'node': "Node not found"
    }
    resp = {
        "itemNotFound": {
            "message": message.get(resource, "The resource could not be found."),
            "code": 404
        }
    }
    if resource == 'loadbalancer' or resource == 'node':
        return resp["itemNotFound"]
    return resp


def invalid_resource(message, response_code=400):
    """
    Returns the given message, and sets the response code to given response
    code.  Defaults response code to 400, if not provided.
    """
    return {"message": message, "code": response_code}


def set_resource_status(updated_time, time_delta, status='ACTIVE',
                        current_timestamp=None):
    """
    Given the updated_time and time delta, if the updated_time + time_delta is
    greater than the current time in UTC, returns the given status; otherwise
    return None.

    :param str updated_time: The time that the server was last updated by a
        client.
    :param int time_delta: The delta, in seconds, from ``updated_time``.
    :param str status: The status to return if the time_delta has expired (i.e.
        the wall clock has advanced more than ``time_delta`` past
        ``updated_time``).
    :param float current_timestamp: The current time, in seconds from the POSIX
        epoch.

    :return: ``status`` or ``None``.
    """
    current_datetime = datetime.utcfromtimestamp(current_timestamp)
    last_updated_datetime = datetime.strptime(updated_time, fmt)
    expiration_interval = timedelta(seconds=int(time_delta))
    expiration_datetime = last_updated_datetime + expiration_interval

    if current_datetime >= expiration_datetime:
        return status


class Matcher(object):
    """
    Class for implementing custom matching.
    """
    def __init__(self, match_fn):
        """
        Set a matcher function on self so that objects can be tested against it.
        """
        self._match_fn = match_fn

    def __eq__(self, other):
        """
        Implements the == comparison based on the custom matcher.
        """
        return self._match_fn(other)
